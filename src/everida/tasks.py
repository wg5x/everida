from __future__ import annotations

import json
import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from everida.agents.product import run_product_pipeline


TASK_STATUSES = {"created", "queued", "running", "completed", "failed", "cancelled", "retrying"}


class TaskNotFoundError(KeyError):
    pass


class TaskRegistry:
    def __init__(self, db_path: str | Path = "outputs/everida_tasks.sqlite3") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def create_product_run(self, params: dict[str, str]) -> dict:
        task_id = f"task_{uuid4().hex[:12]}"
        now = _now()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO tasks (
                    task_id, kind, status, progress, error, params_json,
                    artifacts_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    "product_run",
                    "queued",
                    0,
                    None,
                    json.dumps(params, ensure_ascii=False),
                    "{}",
                    now,
                    now,
                ),
            )
        return self.get(task_id)

    def submit_product_run(self, params: dict[str, str]) -> dict:
        task = self.create_product_run(params)
        thread = threading.Thread(target=self._run_product_task, args=(task["task_id"],), daemon=True)
        thread.start()
        return task

    def get(self, task_id: str) -> dict:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
        if row is None:
            raise TaskNotFoundError(task_id)
        return self._row_to_payload(row)

    def cancel(self, task_id: str) -> dict:
        task = self.get(task_id)
        if task["status"] in {"queued", "created"}:
            self._update(task_id, status="cancelled", progress=0)
        return self.get(task_id)

    def retry(self, task_id: str) -> dict:
        task = self.get(task_id)
        retry_task = self.submit_product_run(task["params"])
        return retry_task

    def _run_product_task(self, task_id: str) -> None:
        task = self.get(task_id)
        if task["status"] == "cancelled":
            return

        self._update(task_id, status="running", progress=5)
        try:
            params = self.get(task_id)["params"]
            result = run_product_pipeline(
                params["spec"],
                params["template"],
                params["sql"],
                params["out_dir"],
            )
        except Exception as exc:
            self._update(task_id, status="failed", progress=100, error=str(exc))
            return

        current = self.get(task_id)
        if current["status"] == "cancelled":
            return
        self._update(
            task_id,
            status="completed",
            progress=100,
            artifacts=result.artifacts,
            error=None,
        )

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress INTEGER NOT NULL,
                    error TEXT,
                    params_json TEXT NOT NULL,
                    artifacts_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _update(
        self,
        task_id: str,
        *,
        status: str | None = None,
        progress: int | None = None,
        error: str | None = None,
        artifacts: dict[str, str] | None = None,
    ) -> None:
        task = self.get(task_id)
        next_status = status or task["status"]
        if next_status not in TASK_STATUSES:
            raise ValueError(f"Unknown task status: {next_status}")
        next_progress = progress if progress is not None else task["progress"]
        next_error = error if error is not None else task["error"]
        next_artifacts = artifacts if artifacts is not None else task["artifacts"]
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE tasks
                SET status = ?, progress = ?, error = ?, artifacts_json = ?, updated_at = ?
                WHERE task_id = ?
                """,
                (
                    next_status,
                    next_progress,
                    next_error,
                    json.dumps(next_artifacts, ensure_ascii=False),
                    _now(),
                    task_id,
                ),
            )

    @staticmethod
    def _row_to_payload(row: sqlite3.Row) -> dict:
        return {
            "task_id": row["task_id"],
            "kind": row["kind"],
            "status": row["status"],
            "progress": row["progress"],
            "error": row["error"],
            "params": json.loads(row["params_json"]),
            "artifacts": json.loads(row["artifacts_json"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }


def _now() -> str:
    return datetime.now(UTC).isoformat()
