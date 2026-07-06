from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from everida.agents.document import parse_document
from everida.agents.product import (
    fill_template,
    generate_sql,
    load_product_json,
    parse_product,
    run_product_pipeline,
    validate_product,
    write_product_json,
)

app = typer.Typer(help="Everida Agent-first business automation CLI.")
document_app = typer.Typer(help="Document Agent commands.")
product_app = typer.Typer(help="Product Agent commands.")

app.add_typer(document_app, name="document")
app.add_typer(product_app, name="product")


@document_app.command("parse")
def document_parse(
    path: Annotated[Path, typer.Argument(help="Input document path.")],
    output_format: Annotated[str, typer.Option("--format", help="json or markdown.")] = "json",
    out: Annotated[Path | None, typer.Option("--out", help="Output file path.")] = None,
):
    parsed = parse_document(path)
    content = parsed.markdown if output_format == "markdown" else parsed.model_dump_json(indent=2)
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")
        typer.echo(str(out))
    else:
        typer.echo(content)


@product_app.command("parse")
def product_parse(
    spec: Annotated[Path, typer.Option("--spec", help="Product requirement DOCX.")],
    out: Annotated[Path, typer.Option("--out", help="Output product JSON.")],
):
    product = parse_product(spec)
    write_product_json(product, out)
    typer.echo(str(out))


@product_app.command("fill-template")
def product_fill_template(
    input_path: Annotated[Path, typer.Option("--input", help="Input product JSON.")],
    template: Annotated[Path, typer.Option("--template", help="Template XLSX.")],
    out: Annotated[Path, typer.Option("--out", help="Filled output XLSX.")],
):
    product = load_product_json(input_path)
    fill_template(product, template, out)
    typer.echo(str(out))


@product_app.command("generate-sql")
def product_generate_sql(
    input_path: Annotated[Path, typer.Option("--input", help="Input product JSON.")],
    out: Annotated[Path, typer.Option("--out", help="Generated SQL path.")],
):
    product = load_product_json(input_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(generate_sql(product), encoding="utf-8")
    typer.echo(str(out))


@product_app.command("validate")
def product_validate(
    spec: Annotated[Path, typer.Option("--spec", help="Product requirement DOCX.")],
    template: Annotated[Path, typer.Option("--template", help="Template XLSX.")],
    sql: Annotated[Path, typer.Option("--sql", help="Existing product SQL.")],
    out: Annotated[Path, typer.Option("--out", help="Validation report path.")],
):
    product = parse_product(spec)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(validate_product(product, template, sql), encoding="utf-8")
    typer.echo(str(out))


@product_app.command("run")
def product_run(
    spec: Annotated[Path, typer.Option("--spec", help="Product requirement DOCX.")],
    template: Annotated[Path, typer.Option("--template", help="Template XLSX.")],
    sql: Annotated[Path, typer.Option("--sql", help="Existing product SQL.")],
    out_dir: Annotated[Path, typer.Option("--out-dir", help="Output directory.")],
    json_output: Annotated[bool, typer.Option("--json", help="Print JSON result.")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", help="Print artifact paths.")] = False,
):
    result = run_product_pipeline(spec, template, sql, out_dir)
    if json_output:
        typer.echo(result.model_dump_json(indent=2))
        return
    typer.echo(f"{result.status}: {result.task_id}")
    if verbose:
        for name, path in result.artifacts.items():
            typer.echo(f"{name}: {path}")
