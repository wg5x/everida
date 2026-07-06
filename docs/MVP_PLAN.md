# Everida MVP 开发计划

## 1. MVP 目标

第一阶段目标是验证 Everida 的 Agent-first 架构，打通：

```text
输入文件
→ Document Agent 解析
→ Product Agent 抽取与生成
→ Validation Layer 校验
→ CLI/API 输出产物
```

MVP 不追求覆盖全部业务模块，优先完成一个可演示、可验证、可扩展的闭环。

## 2. MVP 范围

### 2.1 包含

- Agent Core 基础框架。
- Document Agent。
- Product Agent。
- CLI Adapter。
- API Adapter 完整异步任务系统。
- MCP Tool 接口定义；MCP Server 不作为强制交付。
- 文件解析工具。
- SQL 解析与校验工具。
- 产物管理。
- 示例产品 `120078-中邮未来星年金保险（分红型）` 的完整演示。

### 2.2 暂不包含

- Web 控制台。
- 登录、组织、权限。
- 第三方平台 API。
- 生产 SQL 执行。
- 知识库/RAG 完整产品化。
- 内容运营完整产品化。
- 国外渠道能力。

## 3. 输入与输出

### 3.1 输入

| 文件 | 用途 |
| --- | --- |
| `raw/【已评审需规】120078-未来星年金保险（分红.docx` | 保险产品需求规格书 |
| `raw/产品配置模板.xlsx` | 产品配置模板 |
| `raw/120078_N_1_1.sql` | 已有产品 SQL，用于解析和一致性校验 |

### 3.2 输出

| 产物 | 说明 |
| --- | --- |
| `parsed_document.json` | 文档解析结构 |
| `parsed_document.md` | 文档 Markdown |
| `product.json` | 保险产品结构化配置 |
| `filled.xlsx` | 填充后的配置模板，必须保持原 Excel 样式 |
| `generated.sql` | 生成的 SQL 草稿，覆盖示例 SQL 中全部 38 类表 |
| `sql_inventory.json` | SQL 表、字段、语句清单 |
| `validate_report.md` | 需求/模板/SQL 一致性校验报告 |
| `run_manifest.json` | 本次任务输入、参数、模型、产物索引 |

## 4. MVP 命令

### 4.1 Document Agent

```bash
everida document parse raw/spec.docx --format json --out outputs/parsed_document.json
everida document parse raw/spec.docx --format markdown --out outputs/parsed_document.md
everida document parse raw/template.xlsx --format json --out outputs/template.json
everida document parse raw/product.pdf --format json --out outputs/pdf.json
```

### 4.2 Product Agent

```bash
everida product parse \
  --spec raw/spec.docx \
  --out outputs/product.json

everida product fill-template \
  --input outputs/product.json \
  --template raw/template.xlsx \
  --out outputs/filled.xlsx

everida product generate-sql \
  --input outputs/product.json \
  --out outputs/generated.sql

everida product validate \
  --spec raw/spec.docx \
  --template raw/template.xlsx \
  --sql raw/120078_N_1_1.sql \
  --out outputs/validate_report.md

everida product run \
  --spec raw/spec.docx \
  --template raw/template.xlsx \
  --sql raw/120078_N_1_1.sql \
  --out-dir outputs/120078
```

## 5. API 计划

### 5.1 第一阶段接口

| 接口 | 说明 |
| --- | --- |
| `POST /documents/parse` | 上传并解析文档 |
| `POST /products/parse` | 解析保险产品需求规格书 |
| `POST /products/validate` | 执行三方一致性校验 |
| `POST /products/run` | 一键生成全部产物 |
| `GET /tasks/{task_id}` | 查询任务状态、进度和错误信息 |
| `POST /tasks/{task_id}/cancel` | 取消任务 |
| `POST /tasks/{task_id}/retry` | 重试失败任务 |
| `GET /artifacts/{artifact_id}` | 下载产物 |

### 5.2 API 返回约定

API 第一阶段需要支持完整异步任务生命周期：创建、排队、运行、完成、失败、取消、重试和产物下载。

```json
{
  "task_id": "task_001",
  "status": "completed",
  "progress": 100,
  "error": null,
  "artifacts": [
    {"type": "product_json", "path": "outputs/product.json"},
    {"type": "report", "path": "outputs/validate_report.md"}
  ],
  "issues": []
}
```

## 6. 核心 Schema

### 6.1 Product Schema

```json
{
  "risk_code": "120078",
  "risk_name": "中邮未来星年金保险（分红型）",
  "short_name": "未来星",
  "product_type": "年金保险",
  "bonus_type": "分红型",
  "payment_options": [],
  "insurance_periods": [],
  "liabilities": [],
  "benefit_rules": [],
  "underwriting_rules": [],
  "preservation_rules": [],
  "claim_rules": [],
  "source_refs": []
}
```

### 6.2 Validation Issue Schema

```json
{
  "severity": "warning",
  "category": "missing_benefit_rule",
  "message": "SQL 中未发现逐梦远航金给付责任",
  "source": "spec_docx",
  "target": "product_sql",
  "source_ref": "section: 产品给付责任定义",
  "suggestion": "请确认是否需要补充对应给付责任配置"
}
```

## 7. 开发阶段拆解

### 阶段 0：项目骨架

- 建立 Python 项目结构。
- 配置包管理、测试、lint。
- 定义 `everida-core`、`everida-cli`、`everida-api` 边界。
- 定义统一配置文件。

### 阶段 1：Document Agent

- 实现 DOCX 文本和表格解析。
- 实现 XLSX sheet/table 解析。
- 实现基础 PDF 解析；扫描 PDF/OCR 可先返回明确失败或人工处理建议。
- 输出 Markdown 和 JSON。
- 添加 `source_ref`。

### 阶段 2：Product Agent 抽取

- 定义保险产品 Pydantic schema。
- 实现基于模型的字段抽取。
- 实现字段置信度和来源记录。
- 基于示例文档生成 `product.json`。

### 阶段 3：模板填充

- 解析 `产品配置模板.xlsx`。
- 建立 schema 到模板字段的映射。
- 写入填充后的 Excel。
- 保持原模板 sheet 顺序、列宽、行高、单元格样式、合并单元格、公式、批注和未修改区域内容。
- 标记未填充和需人工确认字段。

### 阶段 4：SQL 解析与生成

- 解析示例 SQL 中的表、字段、产品编码和语句类型。
- 生成 SQL inventory。
- 生成覆盖示例 SQL 全部 38 类表的 SQL 草稿。
- 禁止执行生产 SQL。

### 阶段 5：一致性校验

- 比对 DOCX 抽取结果和 Excel 模板。
- 比对 DOCX 抽取结果和 SQL。
- 比对 Excel 模板和 SQL。
- 输出 Markdown 校验报告。

### 阶段 6：CLI 封装

- 实现 `everida document parse`。
- 实现 `everida product parse`。
- 实现 `everida product fill-template`。
- 实现 `everida product generate-sql`。
- 实现 `everida product validate`。
- 实现 `everida product run`。

### 阶段 7：API 封装

- 实现文件上传。
- 实现异步任务创建、排队、运行、完成、失败、取消、重试状态。
- 实现任务进度、结构化错误和日志摘要。
- 实现产物下载。
- 复用 Agent Core，不重复业务逻辑。

## 8. 验收标准

### 8.1 Document Agent

- 能解析示例 DOCX 并输出章节化 JSON。
- 能解析示例 XLSX 并输出 sheet 结构。
- SQL 解析工具能解析示例 SQL 并输出表清单。
- 输出中包含来源引用。

### 8.2 Product Agent

- 能抽取 `120078`、产品名称、产品类型、保障方案、缴费期间、保险期间、主要给付责任。
- 能输出结构化 `product.json`。
- 能填充配置模板的核心字段，并保持原 Excel 样式。
- 能生成覆盖示例 SQL 全部 38 类表的 SQL 草稿。
- 能输出一致性校验报告。

### 8.3 CLI/API

- CLI 和 API 输出一致产物。
- CLI 支持 `--json`、`--out-dir`、`--verbose`。
- API 支持完整异步任务生命周期、任务状态查询、失败重试、取消和产物下载。

## 9. 里程碑

| 里程碑 | 目标 | 产物 |
| --- | --- | --- |
| M1 | 文档解析闭环 | `parsed_document.json`、`parsed_document.md` |
| M2 | 产品抽取闭环 | `product.json` |
| M3 | 模板与 SQL 初版 | 保持样式的 `filled.xlsx`、覆盖 38 类表的 `generated.sql` |
| M4 | 校验报告 | `validate_report.md` |
| M5 | CLI/API 演示 | `everida product run`、`POST /products/run` |

## 10. 后续扩展

MVP 验证通过后，再按同一套 Agent Core 扩展：

- Knowledge Agent：知识库/RAG、客服辅助。
- Data Agent：Text2SQL 问数。
- Content Agent：内容导入、摘要、改写。
- Report Agent：报告和长图素材生成。
- MCP Server：对外暴露 Everida 工具能力，作为 MVP 后扩展。

## 11. 示例 SQL 38 类表覆盖清单

`generated.sql` MVP 需要覆盖 `raw/120078_N_1_1.sql` 中出现的全部 38 类表：

| 序号 | 表名 |
| --- | --- |
| 1 | `LMRISKAPP` |
| 2 | `LMRISKENTRYITEM` |
| 3 | `LMRISKTORISKTYPE` |
| 4 | `LMEDORCAL` |
| 5 | `LFRISK` |
| 6 | `LMRISKPARAMSDEF` |
| 7 | `LDAUTOAPPROVECONFIG` |
| 8 | `LAWAGECALELEMENT` |
| 9 | `EBSPROTOPROCATALOGDETAIL` |
| 10 | `LMRISKEDORRULE` |
| 11 | `LMRISKBASEPARA` |
| 12 | `LMRISKROLE` |
| 13 | `LMRISKPAY` |
| 14 | `LMRISKBASEPARARELA` |
| 15 | `LMRISKDUTY` |
| 16 | `LMCALMODE` |
| 17 | `LMRISKEDORITEM` |
| 18 | `LMEDORWT` |
| 19 | `LMEDORZT` |
| 20 | `LMEDORZT1` |
| 21 | `LMEDORZTDUTY` |
| 22 | `LMRISKAMNT` |
| 23 | `LMRISK` |
| 24 | `LMRISKAMNTRULE` |
| 25 | `LMDUTY` |
| 26 | `LMDUTYCTRL` |
| 27 | `LMDUTYPAYRELA` |
| 28 | `LMDUTYGETRELA` |
| 29 | `LMDUTYPAY` |
| 30 | `LMDUTYGET` |
| 31 | `LMDUTYGETCLM` |
| 32 | `LMDUTYGETALIVE` |
| 33 | `LMRISKAPPDB` |
| 34 | `LMRISKCOMCTRL` |
| 35 | `LMLOAN` |
| 36 | `LMRISKSORT` |
| 37 | `LMRISKEDORSERVICE` |
| 38 | `LMRISKTORISK` |
