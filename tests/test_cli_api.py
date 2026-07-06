from pathlib import Path
from time import sleep

from fastapi.testclient import TestClient
from typer.testing import CliRunner

from everida.api import app as api_app
from everida.cli import app as cli_app


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "raw" / "【已评审需规】120078-未来星年金保险（分红.docx"
TEMPLATE = ROOT / "raw" / "产品配置模板.xlsx"
SQL = ROOT / "raw" / "120078_N_1_1.sql"


def test_cli_product_run_writes_manifest(tmp_path):
    runner = CliRunner()

    result = runner.invoke(
        cli_app,
        [
            "product",
            "run",
            "--spec",
            str(SPEC),
            "--template",
            str(TEMPLATE),
            "--sql",
            str(SQL),
            "--out-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert (tmp_path / "run_manifest.json").exists()
    assert "completed" in result.output


def test_api_product_run_uses_async_task_lifecycle(tmp_path):
    client = TestClient(api_app)

    response = client.post(
        "/products/run",
        json={
            "spec": str(SPEC),
            "template": str(TEMPLATE),
            "sql": str(SQL),
            "out_dir": str(tmp_path),
        },
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["task_id"]
    assert payload["status"] in {"queued", "running", "completed"}
    assert payload["progress"] in {0, 5, 100}
    assert payload["error"] is None

    task_id = payload["task_id"]
    task = payload
    for _ in range(50):
        task = client.get(f"/tasks/{task_id}").json()
        if task["status"] == "completed":
            break
        sleep(0.05)

    assert task["status"] == "completed"
    assert task["progress"] == 100
    assert "product_json" in task["artifacts"]

    artifact_path = task["artifacts"]["product_json"]
    artifact = client.get(f"/artifacts/{artifact_path}")
    assert artifact.status_code == 200
    assert artifact.json()["risk_code"] == "120078"


def test_api_task_cancel_and_retry_endpoints_exist(tmp_path):
    client = TestClient(api_app)
    response = client.post(
        "/products/run",
        json={
            "spec": str(SPEC),
            "template": str(TEMPLATE),
            "sql": str(SQL),
            "out_dir": str(tmp_path),
        },
    )
    task_id = response.json()["task_id"]

    cancel_response = client.post(f"/tasks/{task_id}/cancel")
    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] in {"cancelled", "running", "completed"}

    retry_response = client.post(f"/tasks/{task_id}/retry")
    assert retry_response.status_code == 200
    assert retry_response.json()["task_id"]
