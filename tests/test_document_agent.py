from pathlib import Path

from everida.agents.document import parse_document
from everida.tools.sql import inspect_sql


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "raw" / "【已评审需规】120078-未来星年金保险（分红.docx"
TEMPLATE = ROOT / "raw" / "产品配置模板.xlsx"
SQL = ROOT / "raw" / "120078_N_1_1.sql"


def test_parse_docx_outputs_markdown_sections_and_source_refs():
    parsed = parse_document(SPEC)

    assert parsed.kind == "docx"
    assert "120078" in parsed.markdown
    assert "未来星" in parsed.markdown
    assert parsed.sections
    assert parsed.sections[0].source_ref.startswith("docx:")


def test_parse_xlsx_outputs_sheet_rows_and_source_refs():
    parsed = parse_document(TEMPLATE)

    assert parsed.kind == "xlsx"
    assert parsed.sheets
    assert parsed.sheets[0].name
    assert parsed.sheets[0].source_ref.startswith("xlsx:")


def test_inspect_sql_outputs_tables_statements_and_product_code():
    inventory = inspect_sql(SQL)

    assert inventory.product_codes == ["120078"]
    assert inventory.statements
    assert inventory.tables
    assert len(inventory.tables) == 38
    assert "LMRISKTORISK" in inventory.tables
    assert all(table == table.upper() for table in inventory.tables)
    assert all(statement.source_ref.startswith("sql:statement:") for statement in inventory.statements)
