import json
from pathlib import Path

from openpyxl import load_workbook

from everida.agents.product import (
    fill_template,
    generate_sql,
    parse_product,
    run_product_pipeline,
    validate_product,
)


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "raw" / "【已评审需规】120078-未来星年金保险（分红.docx"
TEMPLATE = ROOT / "raw" / "产品配置模板.xlsx"
SQL = ROOT / "raw" / "120078_N_1_1.sql"


def test_parse_product_extracts_core_120078_fields():
    product = parse_product(SPEC)

    assert product.risk_code == "120078"
    assert "未来星" in product.risk_name
    assert product.product_type == "年金保险"
    assert "分红型" == product.bonus_type
    assert "趸交" in product.payment_options
    assert "3年" in product.payment_options
    assert "至25岁" in product.insurance_periods
    assert "成长守护金" in product.benefit_rules


def test_parse_product_includes_field_level_evidence():
    product = parse_product(SPEC)

    risk_code_evidence = product.field_evidence["risk_code"]
    assert risk_code_evidence.value == "120078"
    assert risk_code_evidence.source_ref.startswith("docx:")
    assert risk_code_evidence.confidence >= 0.8
    assert "120078" in risk_code_evidence.evidence_text

    payment_evidence = product.field_evidence["payment_options"]
    assert "3年" in payment_evidence.value
    assert payment_evidence.confidence >= 0.6

    benefit_evidence = product.field_evidence["benefit_rules"]
    assert "成长守护金" in benefit_evidence.value
    assert "成长守护金" in benefit_evidence.evidence_text


def test_fill_template_writes_product_summary_sheet(tmp_path):
    product = parse_product(SPEC)
    output = tmp_path / "filled.xlsx"

    fill_template(product, TEMPLATE, output)

    workbook = load_workbook(output)
    assert "Everida产品摘要" in workbook.sheetnames
    sheet = workbook["Everida产品摘要"]
    assert sheet["A1"].value == "字段"
    assert sheet["B2"].value == "120078"


def test_generate_sql_contains_draft_guard_and_core_fields():
    product = parse_product(SPEC)
    sql = generate_sql(product)

    assert "Everida generated draft SQL" in sql
    assert "120078" in sql
    assert "成长守护金" in sql


def test_validate_product_outputs_markdown_report():
    product = parse_product(SPEC)
    report = validate_product(product, TEMPLATE, SQL)

    assert "# Everida 产品一致性校验报告" in report
    assert "120078" in report
    assert "字段证据链" in report
    assert "人工确认项" in report


def test_run_product_pipeline_writes_all_mvp_artifacts(tmp_path):
    result = run_product_pipeline(SPEC, TEMPLATE, SQL, tmp_path)

    expected = {
        "parsed_document_json",
        "parsed_document_markdown",
        "product_json",
        "filled_xlsx",
        "generated_sql",
        "sql_inventory_json",
        "validate_report_markdown",
        "run_manifest_json",
    }
    assert expected == set(result.artifacts)
    for path in result.artifacts.values():
        assert Path(path).exists()

    product = json.loads((tmp_path / "product.json").read_text(encoding="utf-8"))
    manifest = json.loads((tmp_path / "run_manifest.json").read_text(encoding="utf-8"))
    assert product["risk_code"] == "120078"
    assert product["field_evidence"]["risk_code"]["value"] == "120078"
    assert manifest["status"] == "completed"
