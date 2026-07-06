from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from everida.agents.document import parse_document
from everida.agents.product import parse_product, run_product_pipeline, validate_product

app = FastAPI(title="Everida MVP API", version="0.1.0")
TASKS: dict[str, dict] = {}


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
    result = run_product_pipeline(request.spec, request.template, request.sql, request.out_dir)
    payload = result.model_dump()
    TASKS[result.task_id] = payload
    return payload


@app.get("/tasks/{task_id}")
def get_task(task_id: str):
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    return TASKS[task_id]


@app.get("/artifacts/{artifact_id:path}")
def get_artifact(artifact_id: str):
    path = Path(artifact_id)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Artifact not found")
    return {"artifact_id": artifact_id, "content": path.read_text(encoding="utf-8", errors="ignore")}
