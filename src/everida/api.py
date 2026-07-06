from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from everida.agents.document import parse_document
from everida.agents.product import parse_product, validate_product
from everida.tasks import TaskNotFoundError, TaskRegistry

app = FastAPI(title="Everida MVP API", version="0.1.0")
task_registry = TaskRegistry()


class DocumentParseRequest(BaseModel):
    path: str
    format: str = "json"


class ProductParseRequest(BaseModel):
    spec: str


class ProductValidateRequest(BaseModel):
    spec: str
    template: str
    sql: str


class ProductRunRequest(BaseModel):
    spec: str
    template: str
    sql: str
    out_dir: str


@app.post("/documents/parse")
def documents_parse(request: DocumentParseRequest):
    parsed = parse_document(request.path)
    if request.format == "markdown":
        return {"status": "completed", "markdown": parsed.markdown}
    return {"status": "completed", "document": parsed.model_dump()}


@app.post("/products/parse")
def products_parse(request: ProductParseRequest):
    product = parse_product(request.spec)
    return {"status": "completed", "product": product.model_dump()}


@app.post("/products/validate")
def products_validate(request: ProductValidateRequest):
    product = parse_product(request.spec)
    report = validate_product(product, request.template, request.sql)
    return {"status": "completed", "report": report}


@app.post("/products/run")
def products_run(request: ProductRunRequest):
    task = task_registry.submit_product_run(request.model_dump())
    return JSONResponse(status_code=202, content=_public_task(task))


@app.get("/tasks/{task_id}")
def get_task(task_id: str):
    try:
        return _public_task(task_registry.get(task_id))
    except TaskNotFoundError:
        raise HTTPException(status_code=404, detail="Task not found")


@app.post("/tasks/{task_id}/cancel")
def cancel_task(task_id: str):
    try:
        return _public_task(task_registry.cancel(task_id))
    except TaskNotFoundError:
        raise HTTPException(status_code=404, detail="Task not found")


@app.post("/tasks/{task_id}/retry")
def retry_task(task_id: str):
    try:
        return _public_task(task_registry.retry(task_id))
    except TaskNotFoundError:
        raise HTTPException(status_code=404, detail="Task not found")


@app.get("/artifacts/{artifact_id:path}")
def get_artifact(artifact_id: str):
    path = Path(artifact_id)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Artifact not found")
    media_type = _media_type_for(path)
    return FileResponse(path, media_type=media_type, filename=path.name)


def _public_task(task: dict) -> dict:
    return {
        "task_id": task["task_id"],
        "status": task["status"],
        "progress": task["progress"],
        "error": task["error"],
        "artifacts": task["artifacts"],
        "created_at": task["created_at"],
        "updated_at": task["updated_at"],
    }


def _media_type_for(path: Path) -> str:
    if path.suffix == ".json":
        return "application/json"
    if path.suffix == ".md":
        return "text/markdown; charset=utf-8"
    if path.suffix == ".sql":
        return "application/sql; charset=utf-8"
    if path.suffix == ".xlsx":
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return "application/octet-stream"
