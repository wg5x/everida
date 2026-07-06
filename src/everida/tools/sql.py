from __future__ import annotations

from contextlib import contextmanager
import logging
import re
from pathlib import Path
from typing import Any

import sqlglot
from sqlglot import exp

from everida.schemas import SqlInventory, SqlStatement, SqlTableSummary


PRODUCT_CODE_RE = re.compile(r"\b\d{6}\b")


def inspect_sql(path: str | Path) -> SqlInventory:
    file_path = Path(path)
    sql_text = file_path.read_text(encoding="utf-8", errors="ignore")
    raw_statements = [part.strip() for part in sql_text.split(";") if part.strip()]

    statements: list[SqlStatement] = []
    all_tables: set[str] = set()
    summary_by_table: dict[str, dict[str, Any]] = {}
    for index, statement_text in enumerate(raw_statements, start=1):
        statement_type = _statement_type(statement_text)
        with _suppress_sqlglot_warnings():
            tables = _extract_tables(statement_text)
            insert_table, insert_columns, insert_values = _extract_insert_shape(statement_text)
        all_tables.update(tables)
        statements.append(
            SqlStatement(
                statement_type=statement_type,
                tables=tables,
                text=statement_text,
                source_ref=f"sql:statement:{index}",
            )
        )
        for table in tables:
            summary = summary_by_table.setdefault(
                table,
                {
                    "name": table,
                    "statement_types": [],
                    "insert_columns": [],
                    "sample_insert_values": {},
                    "source_ref": f"sql:statement:{index}",
                },
            )
            if statement_type not in summary["statement_types"]:
                summary["statement_types"].append(statement_type)
            if table == insert_table and insert_columns and not summary["insert_columns"]:
                summary["insert_columns"] = insert_columns
                summary["sample_insert_values"] = dict(zip(insert_columns, insert_values, strict=False))

    product_codes = _extract_product_codes(sql_text, file_path)
    return SqlInventory(
        path=str(file_path),
        product_codes=product_codes,
        tables=sorted(all_tables),
        statements=statements,
        table_summaries=[
            SqlTableSummary.model_validate(summary_by_table[table])
            for table in sorted(summary_by_table)
        ],
    )


def _statement_type(statement_text: str) -> str:
    first = statement_text.lstrip().split(None, 1)
    return first[0].upper() if first else "UNKNOWN"


def _extract_tables(statement_text: str) -> list[str]:
    try:
        parsed = sqlglot.parse_one(statement_text)
    except Exception:
        raw_tables = re.findall(r"(?:from|into|update|join|table)\s+([a-zA-Z0-9_.$]+)", statement_text, re.I)
        return sorted({_normalize_table_name(table) for table in raw_tables if _normalize_table_name(table)})
    return sorted({_normalize_table_name(table.name) for table in parsed.find_all(exp.Table) if table.name})


def _normalize_table_name(table_name: str) -> str:
    return table_name.rsplit(".", maxsplit=1)[-1].strip("`\"[]").upper()


def _extract_insert_shape(statement_text: str) -> tuple[str, list[str], list[Any]]:
    try:
        parsed = sqlglot.parse_one(statement_text)
    except Exception:
        return "", [], []
    if not isinstance(parsed, exp.Insert):
        return "", [], []
    schema = parsed.this
    if not isinstance(schema, exp.Schema):
        return "", [], []
    table = schema.this
    table_name = _normalize_table_name(table.name) if isinstance(table, exp.Table) and table.name else ""
    columns = [column.name for column in schema.expressions if hasattr(column, "name") and column.name]
    values = _first_insert_values(parsed)
    return table_name, columns, values


def _first_insert_values(insert: exp.Insert) -> list[Any]:
    values_expression = insert.args.get("expression")
    if not isinstance(values_expression, exp.Values) or not values_expression.expressions:
        return []
    first_tuple = values_expression.expressions[0]
    if not isinstance(first_tuple, exp.Tuple):
        return []
    return [_sql_value(value) for value in first_tuple.expressions]


def _sql_value(value: exp.Expression) -> Any:
    if isinstance(value, exp.Null):
        return None
    if isinstance(value, exp.Literal):
        return value.this
    return value.sql()


@contextmanager
def _suppress_sqlglot_warnings():
    logger = logging.getLogger("sqlglot")
    was_disabled = logger.disabled
    logger.disabled = True
    try:
        yield
    finally:
        logger.disabled = was_disabled


def _extract_product_codes(sql_text: str, path: Path) -> list[str]:
    filename_codes = PRODUCT_CODE_RE.findall(path.name)
    if filename_codes:
        return sorted(set(filename_codes))

    counts: dict[str, int] = {}
    for code in PRODUCT_CODE_RE.findall(sql_text):
        if code.startswith("0") or code.startswith("8"):
            continue
        counts[code] = counts.get(code, 0) + 1
    if not counts:
        return []
    max_count = max(counts.values())
    return sorted(code for code, count in counts.items() if count == max_count)
