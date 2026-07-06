# Everida Agent-first 业务自动化能力平台 PRD

## 1. 文档信息

| 项目 | 内容 |
| --- | --- |
| 产品名称 | Everida |
| 产品形态 | Agent Core + CLI Adapter + API Adapter + MCP Tools |
| 文档类型 | 产品需求文档 PRD |
| 版本 | v0.2 |
| 来源 | `raw/需求池.md`、`raw/【已评审需规】120078-未来星年金保险（分红.docx`、`raw/产品配置模板.xlsx`、`raw/120078_N_1_1.sql` |
| 状态 | 已按 Agent-first 方向重构 |

## 2. 产品背景

原始需求覆盖内容运营、客服辅助、知识库、图文生成、Text2SQL、保险产品配置、舆情/差评监控等多个方向。经过需求收敛后，Everida 不应优先定义为一个固定 Web 平台，而应定义为一套可被智能体、CLI、后端服务共同调用的业务自动化能力层。

保险产品配置相关新增文件提供了一个非常适合 MVP 的真实闭环：输入需求规格书、配置模板和 SQL 文件，输出结构化配置、SQL 草稿和一致性校验报告。该场景具备输入明确、输出可验证、人工确认边界清晰的特点，适合作为 Agent Core 的第一条落地链路。

## 3. 产品定位

Everida 是一个 **Agent-first 的业务自动化能力平台**。它将文档解析、知识库检索、内容处理、数据问答、产品配置生成、报告生成等能力封装为可组合的 Agent 能力，并通过 CLI、API 和 MCP 工具对外提供服务。

### 3.1 核心原则

- **Agent-first**：业务能力优先封装为 Agent 可调用的工具和流程，而不是先做页面。
- **Model-first**：尽量使用模型能力完成语义理解、字段抽取、规则识别、内容生成和报告生成。
- **API-light**：MVP 不依赖第三方平台业务 API，不优先接小红书、抖音、大众点评、Reddit、Facebook 等平台 API。
- **CLI/API 双适配**：同一套 Agent Core 同时支持命令行、本地批处理、后端接口和未来 Web 控制台。
- **MCP 工具化**：网页采集、浏览器快照、文件解析、SQL 校验等底层能力作为 Agent 可调用的 MCP 工具，不作为强绑定业务模块。
- **结构化输出**：所有核心能力必须支持 JSON 输出，方便 Agent 编排、CLI 管道和 API 调用。
- **可验证产物**：生成结果必须输出可追踪产物，例如 JSON、Markdown 报告、Excel、SQL、日志和校验报告。
- **Human-in-the-loop**：涉及 SQL 执行、外部平台发布、批量触达等高风险动作时，默认只生成草稿和建议，由人工确认。

### 3.2 目标用户

| 用户角色 | 典型需求 |
| --- | --- |
| 业务分析/产品配置人员 | 从需求文档生成结构化配置、SQL 草稿和校验报告 |
| 运营人员 | 导入内容、分析爆款、改写文案、生成报告 |
| 销售/客服人员 | 导入报价、合同、素材和聊天记录，获得回复建议 |
| 数据分析人员 | 基于 schema 和业务问题生成 SQL、解释查询结果 |
| 开发者/集成方 | 通过 CLI、API 或 MCP 调用 Everida 能力 |
| 企业智能体 | 调用 Everida 工具完成文档理解、检索、生成、校验和产物管理 |

## 4. 总体架构

```text
Everida Agent Core
├─ CLI Adapter
├─ API Adapter
├─ MCP Adapter
├─ Document Agent
├─ Product Agent
├─ Knowledge Agent
├─ Content Agent
├─ Data Agent
├─ Report Agent
├─ Artifact Manager
└─ Validation Layer
```

### 4.1 Agent Core

Agent Core 负责统一工具注册、任务编排、模型调用、结构化输出、产物管理、错误处理和审计记录。

### 4.2 CLI Adapter

CLI Adapter 将 Agent Core 暴露为本地命令，适合本地文件处理、批处理、私有化环境和开发调试。

### 4.3 API Adapter

API Adapter 将同一套能力暴露为 HTTP API，供前端、后端系统和第三方业务系统调用。

### 4.4 MCP Tools

MCP Tools 是 Agent 的底层工具层，包括文件读取、文档解析、网页采集、浏览器快照、搜索、SQL 校验和产物写入。爬虫/采集能力不作为独立业务模块，而是 Agent 调用的工具。

## 5. 产品模块

| 模块 | 优先级 | 定位 |
| --- | --- | --- |
| Document Agent | P0 | 通用文档解析、OCR、表格抽取、分块、结构化抽取 |
| Product Agent | P0 | 保险产品需求解析、配置模板填充、SQL 生成、一致性校验 |
| Knowledge Agent | P1 | 知识库导入、索引、检索、问答、客服辅助 |
| Data Agent | P1 | Text2SQL、schema 理解、只读 SQL 校验、问数解释 |
| Content Agent | P1 | 内容导入、清洗、摘要、标签、情绪分析、文案改写 |
| Report Agent | P1 | 基于文档、知识库、Excel、内容数据生成报告和长图素材 |
| Monitor Agent | P2 | 基于用户导入或采集内容做差评/舆情监控与摘要 |
| Web Console | P3 | 后续可选控制台，不进入 MVP |
| 国外渠道自动化 | 暂缓 | Reddit、Facebook、Instagram、LinkedIn 等不进入当前阶段 |

## 6. MVP 范围

### 6.1 MVP 目标

第一阶段打通 **Document Agent + Product Agent + CLI/API + MCP 工具层**，验证 Everida 的 Agent-first 架构是否可行。

### 6.2 MVP 包含

- 通用文档解析：支持 PDF、扫描 PDF、DOCX、XLSX、图片等输入。
- 结构化抽取：基于模型和 schema 输出 JSON。
- 保险产品配置生成：从需求规格书抽取产品、责任、给付、缴费、保全、理赔、投核保规则。
- 产品配置模板填充：将抽取结果写入 Excel 模板或生成中间 JSON，`filled.xlsx` 必须保持原模板样式。
- 产品 SQL 生成：基于结构化配置生成 SQL 草稿，MVP 需要覆盖示例 SQL 中的全部 38 类表。
- 一致性校验：比对需求文档、配置模板、SQL 文件之间的差异。
- CLI 命令：提供本地命令行调用。
- API 接口：第一阶段即提供完整异步任务系统，包括任务创建、状态查询、产物下载和错误追踪。
- MCP 工具接口：定义文件解析、网页采集、SQL 校验、产物写入等底层工具接口；MCP Server 可后续实现。

### 6.3 MVP 暂不包含

- Web 控制台。
- 用户登录、组织空间和复杂权限体系。
- 第三方平台 API 接入。
- 自动发布、自动评论、自动私信、矩阵号操作。
- 生产数据库 SQL 执行。
- 国外渠道自动化运营。

## 7. 功能需求

### 7.1 Document Agent

#### 7.1.1 文档解析

系统支持解析：

- PDF。
- 扫描 PDF。
- DOCX。
- XLSX。
- PPTX。
- 图片。
- HTML/Markdown/纯文本。

#### 7.1.2 输出格式

Document Agent 需要支持输出：

- Markdown。
- 结构化 JSON。
- 表格 JSON。
- 图片/页面引用。
- 文档 chunk。
- 字段抽取结果。

#### 7.1.3 模型增强抽取

模型 API 用于语义理解和字段抽取，包括：

- 识别文档主题和章节结构。
- 提取关键字段。
- 识别表格语义。
- 识别规则、条件、例外和约束。
- 生成摘要和待确认问题。

#### 7.1.4 验收标准

- 输入 DOCX 后，可输出 Markdown 和章节化 JSON。
- 输入 XLSX 后，可输出 sheet、行列、表头和数据 JSON。
- 输入 PDF 后，可输出文本、表格和页面引用。
- 对扫描 PDF 或图片 PDF，可给出 OCR 结果或明确失败原因。
- 输出字段包含 `source_ref` 和 `confidence`。

### 7.2 Product Agent

#### 7.2.1 保险产品需求解析

Product Agent 从保险产品需求规格书中抽取：

- 产品基础信息：险种编码、险种名称、简称、险种类型、主附险标记、长短险标记。
- 产品形态：缴费方式、缴费期间、保险期间、保障方案。
- 责任定义：责任代码、责任名称、是否必选、保额保费计算方式。
- 给付责任：成长守护金、大学教育金、深造教育金、有成关爱金、逐梦远航金、满期保险金、身故保险金、豁免责任等。
- 投核保规则：投保年龄、性别限制、最低保额、保额递增单位。
- 保全规则：退保、减保、年金领取、现金价值、自动复核规则。
- 理赔规则：身故责任、理赔算法、风险保额。
- 外围系统：核心系统、产品工厂、智能两核、保单服务域、保单打印、电子印章、统信报送、反洗钱、财务等。

#### 7.2.2 配置模板填充

系统支持将抽取结果映射到产品配置模板。生成的 `filled.xlsx` 必须保持原 Excel 模板样式，包括 sheet 顺序、列宽、行高、单元格样式、合并单元格、公式、批注和未修改区域内容。模板包含：

- 产品基础信息。
- 录入项配置。
- 参数定义。
- 角色保额配置。
- 责任定义。
- 给付责任。
- 缴费计划。
- 计算规则。

#### 7.2.3 SQL 生成

系统根据确认后的结构化配置生成产品工厂 SQL 草稿。MVP 需要覆盖示例 SQL 中出现的全部 38 类表，并至少按以下业务域组织：

- 产品主数据表。
- 界面录入项表。
- 责任与给付表。
- 缴费计划表。
- 保全规则表。
- 计算规则表。
- 风险保额与销售控制表。
- 销售、限额、保费测算、财务、外围系统相关配置表。

#### 7.2.4 一致性校验

系统支持需求文档、Excel 模板、SQL 文件三方比对：

- 产品编码与名称是否一致。
- 录入项是否齐全。
- 给付责任是否遗漏。
- 缴费期间、保险期间、投保年龄、最低保额是否一致。
- 保全、理赔、财务和外围系统配置是否遗漏。
- SQL 是否存在明显语法错误、重复删除/插入或缺失关键表。

#### 7.2.5 示例产品

MVP 示例产品为 `120078-中邮未来星年金保险（分红型）`：

- 产品类型：年金保险、分红型、个险、主险、长险。
- 保障方案：保障方案一、保障方案二。
- 缴费方式：趸交、年交。
- 缴费期间：趸交、3 年、5 年、10 年。
- 保险期间：至 25 岁、至 30 岁、30 年。
- 主要给付：成长守护金、大学教育金、深造教育金、有成关爱金、逐梦远航金、满期保险金、身故保险金、投保人意外身故豁免保险费。
- 销售方式：按保额销售，保额 1000 元递增。

#### 7.2.6 验收标准

- 能从示例 DOCX 中抽取产品基础信息和主要规则。
- 能基于示例 XLSX 识别模板结构。
- 能解析示例 SQL 中涉及的核心表和产品编码。
- 能输出 `product.json`、`filled.xlsx`、`generated.sql`、`validate_report.md`。
- `filled.xlsx` 保持原 Excel 模板样式和未修改区域内容。
- `generated.sql` 覆盖示例 SQL 中出现的全部 38 类表。
- 能标记缺失字段、不一致字段和人工确认项。

### 7.3 Knowledge Agent

Knowledge Agent 负责知识库导入、索引、检索和问答。MVP 只做设计预留，不作为首个开发闭环。

### 7.4 Content Agent

Content Agent 负责导入内容、清洗、分类、摘要、情绪分析和文案改写。MVP 不依赖平台 API，输入以文件、URL、复制文本、截图和人工导出数据为主。

### 7.5 Data Agent

Data Agent 负责 schema 解析、Text2SQL、只读 SQL 校验和问数解释。MVP 阶段只做架构预留。

### 7.6 Report Agent

Report Agent 负责基于文档、知识库、Excel 和内容分析结果生成报告素材、长图文案和结构化摘要。MVP 阶段只做架构预留。

### 7.7 MCP 工具层

#### 7.7.1 文件工具

- `file.read`：读取本地文件。
- `file.write`：写入产物。
- `file.convert`：转换文档格式。

#### 7.7.2 文档工具

- `document.parse`：解析文档。
- `document.ocr`：OCR 识别。
- `document.chunk`：文档分块。

#### 7.7.3 采集工具

采集工具是 Agent 的“手和眼睛”，不是业务模块。

- `web.fetch_url`：获取公开网页内容。
- `web.extract_readable`：提取正文并转 Markdown。
- `web.screenshot`：页面快照。
- `web.batch_collect`：批量采集 URL。

#### 7.7.4 SQL 工具

- `sql.parse`：解析 SQL。
- `sql.validate`：语法和安全校验。
- `sql.diff`：对比 SQL 与结构化配置。

#### 7.7.5 产物工具

- `artifact.write_json`。
- `artifact.write_markdown`。
- `artifact.write_excel`。
- `artifact.write_sql`。

## 8. CLI 需求

### 8.1 Document CLI

```bash
everida document parse input.pdf --format json --out parsed.json
everida document parse input.docx --format markdown --out parsed.md
everida document extract input.pdf --schema schema.json --out extracted.json
everida document chunk input.pdf --strategy heading --out chunks.json
```

### 8.2 Product CLI

```bash
everida product parse --spec spec.docx --out product.json
everida product fill-template --input product.json --template template.xlsx --out filled.xlsx
everida product generate-sql --input product.json --out generated.sql
everida product validate --spec spec.docx --template template.xlsx --sql generated.sql --out validate_report.md
everida product run --spec spec.docx --template template.xlsx --sql existing.sql --out-dir outputs/
```

### 8.3 通用参数

所有命令应支持：

- `--json`：以 JSON 输出运行结果。
- `--out` / `--out-dir`：指定产物输出位置。
- `--model`：指定模型。
- `--config`：指定配置文件。
- `--dry-run`：只预览，不写入高风险产物。
- `--verbose`：输出详细日志。

## 9. API 需求

### 9.1 文档接口

- `POST /documents/parse`：上传文件并解析。
- `POST /documents/extract`：按 schema 抽取字段。
- `GET /tasks/{task_id}`：查询任务状态。
- `GET /artifacts/{artifact_id}`：下载产物。

### 9.2 产品接口

- `POST /products/parse`：解析产品需求规格书。
- `POST /products/fill-template`：填充配置模板。
- `POST /products/generate-sql`：生成 SQL 草稿。
- `POST /products/validate`：执行一致性校验。
- `POST /products/run`：一键执行 parse、fill、generate、validate。

### 9.3 API 约束

- 第一阶段提供完整异步任务系统。
- 所有耗时任务必须异步执行。
- API 返回 `task_id`、任务状态、进度、错误信息和 artifact id。
- 支持任务状态查询、失败重试、任务取消和产物下载。
- 所有接口支持结构化错误码。
- 不提供生产库 SQL 执行接口。

## 10. 数据对象

| 对象 | 说明 |
| --- | --- |
| AgentTask | Agent 执行任务 |
| ToolCall | 工具调用记录 |
| Artifact | 产物记录 |
| ParsedDocument | 解析后的文档结构 |
| DocumentChunk | 文档分块 |
| ExtractionSchema | 抽取 schema |
| ExtractionResult | 字段抽取结果 |
| InsuranceProduct | 保险产品基础信息 |
| ProductLiability | 产品责任 |
| BenefitRule | 给付责任 |
| PaymentPlan | 缴费计划 |
| UnderwritingRule | 投核保规则 |
| PreservationRule | 保全规则 |
| ClaimRule | 理赔规则 |
| ProductConfigTemplate | 产品配置模板 |
| ProductSqlScript | 产品 SQL 脚本 |
| ValidationIssue | 校验问题 |
| ValidationReport | 校验报告 |

## 11. 非功能需求

### 11.1 可追溯性

- 抽取字段必须尽量包含 `source_ref`。
- 产物必须记录输入文件、模型、参数和生成时间。
- 校验报告必须能定位到具体字段或 SQL 表。

### 11.2 安全性

- 本地文件默认不上传第三方平台，除非用户配置模型 API。
- SQL 默认只生成和校验，不直接执行。
- API 需限制文件大小、任务超时和并发数。

### 11.3 可扩展性

- Agent、Tool、Adapter 解耦。
- 文档解析器可替换。
- 向量库可从 Milvus Lite 平滑迁移到 Milvus Standalone。
- 模型供应商可配置。

### 11.4 稳定性

- 长任务支持状态查询和失败重试。
- 输出产物失败时保留中间结果。
- 模型抽取失败时返回可解释错误和人工处理建议。

## 12. 成功指标

### 12.1 MVP 指标

- 示例产品文档可成功解析并输出结构化 JSON。
- 示例 Excel 模板可被识别并生成填充结果，且填充文件保持原模板样式。
- 示例 SQL 可被解析并输出全部 38 类表清单。
- 生成 SQL 草稿覆盖示例 SQL 中的全部 38 类表。
- 三方一致性校验报告可指出主要一致项、缺失项和人工确认项。
- CLI 和 API 均能复用同一套 Agent Core。
- API 支持完整异步任务生命周期：创建、排队、运行、完成、失败、取消、重试、产物下载。

### 12.2 质量指标

- 产品基础字段抽取准确率达到 90% 以上。
- 关键责任/给付规则抽取准确率达到 80% 以上。
- 校验报告中人工确认项可解释、可定位。
- CLI 单次任务输出完整产物目录。

## 13. 风险与应对

| 风险 | 说明 | 应对 |
| --- | --- | --- |
| 模型幻觉 | 模型可能生成不存在的字段或规则 | 强制 source_ref、confidence、规则校验和人工确认 |
| PDF 复杂 | 扫描件、复杂表格、页眉页脚影响解析 | Docling 为主，MinerU/Marker 作为 fallback |
| SQL 风险 | 产品 SQL 涉及核心业务表 | MVP 只生成和校验，不执行生产 SQL |
| 模板变化 | Excel 模板可能多版本变化 | 设计模板映射层和版本号 |
| API 依赖过重 | 外部平台 API 不稳定或接入成本高 | MVP 不依赖平台 API，优先文件和模型能力 |
| 采集合规 | 网页采集可能涉及平台限制 | 只采集公开/授权内容，爬虫作为 MCP 工具且不绕风控 |

## 14. 已确认决策与待确认问题

### 14.1 已确认决策

1. API 第一阶段需要完整异步任务系统。
2. `filled.xlsx` 必须保持原 Excel 模板样式。
3. SQL 草稿需要覆盖示例 SQL 中出现的全部 38 类表。

### 14.2 待确认问题

1. MVP 是否只聚焦 `Document Agent + Product Agent`？
2. 模型 API 首选供应商和模型是什么？
3. PDF 解析是否需要优先支持扫描件 OCR？
4. MCP Server 是否进入 MVP，还是 MVP 只定义 MCP 工具接口后续实现？
