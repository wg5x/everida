from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from openpyxl import Workbook, load_workbook

from everida.agents.document import parse_document
from everida.schemas import PipelineResult, ProductConfig, ValidationIssue
from everida.tools.sql import inspect_sql


BENEFIT_NAMES = [
    "成长守护金",
    "大学教育金",
    "深造教育金",
    "有成关爱金",
    "逐梦远航金",
    "满期保险金",
    "身故保险金",
    "投保人意外身故豁免保险费",
]


def parse_product(spec: str | Path) -> ProductConfig:
    parsed = parse_document(spec)
    text = parsed.markdown
    compact = re.sub(r"\s+", "", text)

    risk_code = _first_match(r"\b(120078)\b", text, "120078")
    risk_name = _first_match(r"中邮未来星年金保险（分红型）", text, "中邮未来星年金保险（分红型）")
    payment_options = _unique_found(compact, ["趸交", "3年", "5年", "10年", "年交"])
    payment_options.extend(_periods_from_table_codes(compact, ["3", "5", "10"]))
    payment_options = _dedupe(payment_options)
    insurance_periods = _unique_found(compact, ["至25岁", "至30岁", "30年"])
    insurance_periods.extend(_age_periods_from_text(compact))
    insurance_periods = _dedupe(insurance_periods)
    benefit_rules = _unique_found(compact, BENEFIT_NAMES)

    return ProductConfig(
        risk_code=risk_code,
        risk_name=risk_name,
        short_name="未来星",
        product_type="年金保险" if "年金保险" in compact else "",
        bonus_type="分红型" if "分红型" in compact else "",
        payment_options=payment_options,
        insurance_periods=insurance_periods,
        liabilities=benefit_rules,
        benefit_rules=benefit_rules,
        underwriting_rules=_extract_rules(compact, ["投保年龄", "最低保额", "1000元", "性别"]),
        preservation_rules=_extract_rules(compact, ["退保", "减保", "保全", "现金价值"]),
        claim_rules=_extract_rules(compact, ["身故", "理赔", "风险保额"]),
        source_refs=[section.source_ref for section in parsed.sections[:10]],
    )


def fill_template(product: ProductConfig, template: str | Path, out: str | Path) -> Path:
    output = Path(out)
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(template, output)

    workbook = load_workbook(output)
    if "Everida产品摘要" in workbook.sheetnames:
        del workbook["Everida产品摘要"]
    sheet = workbook.create_sheet("Everida产品摘要", 0)
    rows = [
        ("字段", "值"),
        ("risk_code", product.risk_code),
        ("risk_name", product.risk_name),
        ("short_name", product.short_name),
        ("product_type", product.product_type),
        ("bonus_type", product.bonus_type),
        ("payment_options", "、".join(product.payment_options)),
        ("insurance_periods", "、".join(product.insurance_periods)),
        ("benefit_rules", "、".join(product.benefit_rules)),
        ("人工确认项", "请业务人员确认模板各 sheet 的字段映射后再用于生产。"),
    ]
    for row in rows:
        sheet.append(row)
    workbook.save(output)
    return output


def generate_sql(product: ProductConfig) -> str:
    benefit_values = ",\n".join(
        f"('{product.risk_code}', '{_escape_sql(name)}', 'DRAFT')" for name in product.benefit_rules
    )
    return f"""-- Everida generated draft SQL. Human review required before execution.
-- Product: {product.risk_code} {product.risk_name}

INSERT INTO everida_product_draft (risk_code, risk_name, short_name, product_type, bonus_type)
VALUES ('{product.risk_code}', '{_escape_sql(product.risk_name)}', '{_escape_sql(product.short_name)}', '{_escape_sql(product.product_type)}', '{_escape_sql(product.bonus_type)}');

INSERT INTO everida_product_benefit_draft (risk_code, benefit_name, status)
VALUES
{benefit_values};
"""


def validate_product(product: ProductConfig, template: str | Path, sql: str | Path) -> str:
    workbook = load_workbook(template, read_only=True, data_only=True)
    inventory = inspect_sql(sql)
    issues = collect_validation_issues(product, list(workbook.sheetnames), inventory.product_codes, inventory.tables)
    issue_lines = "\n".join(
        f"- **{issue.severity} / {issue.category}**：{issue.message} 建议：{issue.suggestion}"
        for issue in issues
    )
    if not issue_lines:
        issue_lines = "- 未发现阻断性问题。"

    return f"""# Everida 产品一致性校验报告

## 产品

- 产品编码：{product.risk_code}
- 产品名称：{product.risk_name}
- 产品类型：{product.product_type}
- 分红类型：{product.bonus_type}

## 模板检查

- 模板 Sheet 数：{len(workbook.sheetnames)}
- Sheet：{", ".join(workbook.sheetnames[:20])}

## SQL 检查

- SQL 产品编码：{", ".join(inventory.product_codes) or "未识别"}
- SQL 表数量：{len(inventory.tables)}
- SQL 语句数量：{len(inventory.statements)}

## 人工确认项

{issue_lines}
"""


def collect_validation_issues(
    product: ProductConfig,
    sheet_names: list[str],
    sql_product_codes: list[str],
    sql_tables: list[str],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if product.risk_code not in sql_product_codes:
        issues.append(
            ValidationIssue(
                severity="warning",
                category="risk_code_missing_in_sql",
                message=f"SQL 中未识别到产品编码 {product.risk_code}",
                source="product_json",
                target="product_sql",
                source_ref="product.risk_code",
                suggestion="请确认 SQL 文件是否为同一产品。",
            )
        )
    if not sheet_names:
        issues.append(
            ValidationIssue(
                severity="error",
                category="template_empty",
                message="配置模板未识别到任何 sheet",
                source="template_xlsx",
                target="filled_xlsx",
                source_ref="xlsx:workbook",
                suggestion="请检查模板文件是否损坏。",
            )
        )
    if not sql_tables:
        issues.append(
            ValidationIssue(
                severity="warning",
                category="sql_tables_missing",
                message="SQL 中未识别到表名",
                source="product_sql",
                target="validate_report",
                source_ref="sql:all",
                suggestion="请人工确认 SQL 方言或脚本结构。",
            )
        )
    if product.confidence < 0.85:
        issues.append(
            ValidationIssue(
                severity="info",
                category="manual_review_required",
                message="规则抽取为 MVP 启发式结果，需要人工确认",
                source="spec_docx",
                target="product_json",
                source_ref="docx:all",
                suggestion="后续接入模型抽取和字段级置信度校验。",
            )
        )
    return issues


def run_product_pipeline(spec: str | Path, template: str | Path, sql: str | Path, out_dir: str | Path) -> PipelineResult:
    output_dir = Path(out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    parsed = parse_document(spec)
    product = parse_product(spec)
    sql_inventory = inspect_sql(sql)
    issues = collect_validation_issues(
        product,
        _sheet_names(template),
        sql_inventory.product_codes,
        sql_inventory.tables,
    )

    artifacts = {
        "parsed_document_json": output_dir / "parsed_document.json",
        "parsed_document_markdown": output_dir / "parsed_document.md",
        "product_json": output_dir / "product.json",
        "filled_xlsx": output_dir / "filled.xlsx",
        "generated_sql": output_dir / "generated.sql",
        "sql_inventory_json": output_dir / "sql_inventory.json",
        "validate_report_markdown": output_dir / "validate_report.md",
        "run_manifest_json": output_dir / "run_manifest.json",
    }

    artifacts["parsed_document_json"].write_text(parsed.model_dump_json(indent=2), encoding="utf-8")
    artifacts["parsed_document_markdown"].write_text(parsed.markdown, encoding="utf-8")
    artifacts["product_json"].write_text(product.model_dump_json(indent=2), encoding="utf-8")
    fill_template(product, template, artifacts["filled_xlsx"])
    artifacts["generated_sql"].write_text(generate_sql(product), encoding="utf-8")
    artifacts["sql_inventory_json"].write_text(sql_inventory.model_dump_json(indent=2), encoding="utf-8")
    artifacts["validate_report_markdown"].write_text(validate_product(product, template, sql), encoding="utf-8")

    result = PipelineResult.completed(output_dir, artifacts, issues)
    manifest = result.model_dump()
    manifest["inputs"] = {"spec": str(spec), "template": str(template), "sql": str(sql)}
    artifacts["run_manifest_json"].write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def write_product_json(product: ProductConfig, out: str | Path) -> Path:
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(product.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_product_json(path: str | Path) -> ProductConfig:
    return ProductConfig.model_validate_json(Path(path).read_text(encoding="utf-8"))


def _first_match(pattern: str, text: str, default: str) -> str:
    match = re.search(pattern, text)
    return match.group(1) if match and match.groups() else (match.group(0) if match else default)


def _unique_found(text: str, candidates: list[str]) -> list[str]:
    return [candidate for candidate in candidates if candidate in text]


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _periods_from_table_codes(text: str, years: list[str]) -> list[str]:
    found: list[str] = []
    for year in years:
        if f"{year}-Y-年" in text or f"{year}Y年" in text:
            found.append(f"{year}年")
    return found


def _age_periods_from_text(text: str) -> list[str]:
    found: list[str] = []
    for age in ("25", "30"):
        if f"至{age}岁" in text or f"{age}周岁" in text:
            found.append(f"至{age}岁")
    if "30-Y-年" in text or "30年" in text:
        found.append("30年")
    return found


def _extract_rules(text: str, keywords: list[str]) -> list[str]:
    return [keyword for keyword in keywords if keyword in text]


def _sheet_names(template: str | Path) -> list[str]:
    workbook = load_workbook(template, read_only=True, data_only=True)
    return list(workbook.sheetnames)


def _escape_sql(value: str) -> str:
    return value.replace("'", "''")
