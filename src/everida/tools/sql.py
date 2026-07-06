from __future__ import annotations

import re
from pathlib import Path

import sqlglot
from sqlglot import exp

from everida.schemas import SqlInventory, SqlStatement


PRODUCT_CODE_RE = re.compile(r"\b\d{6}\b")


def inspect_sql(path: str | Path) -> SqlInventory:
    file_path = Path(path)
    sql_text = file_path.read_text(encoding="utf-8", errors="ignore")
    raw_statements = [part.strip() for part in sql_text.split(";") if part.strip()]

    statements: list[SqlStatement] = []
    all_tables: set[str] = set()
    for index, statement_text in enumerate(raw_statements, start=1):
        statement_type = _statement_type(statement_text)
        tables = _extract_tables(statement_text)
        all_tables.update(tables)
        statements.append(
            SqlStatement(
                statement_type=statement_type,
                tables=tables,
                text=statement_text,
                source_ref=f"sql:statement:{index}",
            )
        )

    product_codes = _extract_product_codes(sql_text, file_path)
    return SqlInventory(
        path=str(file_path),
        product_codes=product_codes,
        tables=sorted(all_tables),
        statements=statements,
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
