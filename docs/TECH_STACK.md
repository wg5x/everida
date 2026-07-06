# Everida 技术选型文档

## 1. 选型原则

- **Agent-first**：先实现可被 Agent 调用的能力，再适配 CLI/API/Web。
- **Model-first**：业务理解、字段抽取、规则识别、内容生成尽量使用模型能力。
- **API-light**：MVP 不依赖第三方业务平台 API。
- **可验证**：模型输出必须经过 schema、规则、SQL、文件产物校验。
- **本地优先**：支持本地 CLI、私有化文件处理和可迁移存储。
- **可替换**：模型、文档解析器、向量库、爬虫工具都应可替换。

## 2. 推荐技术栈

| 层级 | 推荐 | 说明 |
| --- | --- | --- |
| Agent Core | Pydantic AI | typed tools、结构化输出、和 Pydantic/FastAPI 生态一致 |
| 复杂流程 | LangGraph | 后续用于长流程、状态机、人工确认、失败恢复 |
| CLI | Typer | Python CLI 快速开发，类型提示友好 |
| API | FastAPI | 和 Pydantic 深度集成，适合异步任务接口 |
| MCP | MCP Python SDK | 将工具暴露给外部智能体调用 |
| 文档解析 | Docling | 默认文档解析器，覆盖 PDF/DOCX/XLSX/PPTX/图片等 |
| 复杂 PDF fallback | MinerU / Marker | 复杂 PDF、扫描件、表格、公式场景补充 |
| Office 兜底 | python-docx / openpyxl | 对 DOCX/XLSX 做精确结构读取和模板写入 |
| RAG | LlamaIndex | 文档 ingestion、chunk、retriever、RAG pipeline |
| 向量库 | Milvus Lite / Milvus | MVP 本地 Milvus Lite，生产切 Milvus Standalone/Distributed |
| SQL 解析 | SQLGlot | SQL AST 解析、方言处理、基础校验 |
| SQL 风格检查 | SQLFluff | SQL lint 和规范检查 |
| 网页采集工具 | Crawlee Python / Playwright | 作为 MCP 工具，不作为业务模块 |
| LLM-ready 采集 | Firecrawl / Crawl4AI | 网页转 Markdown、正文抽取，可作为可选工具 |
| 任务执行 | SQLite-backed task registry + worker | MVP 需完整异步任务生命周期；后续再接 Redis/RQ/Celery 或 Prefect/Temporal |

## 3. Agent Core 选择

### 3.1 MVP 推荐：Pydantic AI

选择理由：

- 天然支持结构化输出。
- 能用 Pydantic schema 约束模型结果。
- 适合把工具封装为 typed tools。
- 方便 CLI 和 API 共用同一套 core service。
- 上手成本低于完整工作流框架。

### 3.2 后续增强：LangGraph

当出现以下需求时引入 LangGraph：

- 多步骤长流程需要恢复。
- 任务中间需要人工确认。
- Agent 状态需要持久化。
- 多 Agent 协作。
- 复杂分支、重试、回滚。

### 3.3 MCP 角色

MCP 不替代 Agent Core，而是工具暴露层：

- 对内：Everida Agent 调用 MCP 工具。
- 对外：其他 Agent 调用 Everida 工具。
- 工具示例：`document.parse`、`web.fetch_url`、`sql.validate`、`artifact.write_json`。

## 4. 文档解析方案

### 4.1 推荐链路

```text
文件输入
→ Docling / MinerU / Marker / Office parser
→ Markdown + Tables + Images + Layout JSON
→ chunk
→ 模型按 schema 抽取
→ 规则校验
→ 产物输出
```

### 4.2 为什么不是只用模型 API

- Office/PDF 有表格、合并单元格、页眉页脚、扫描图像等复杂结构。
- 保险产品配置需要字段来源追溯。
- 模型可能漏字段或幻觉。
- 代码解析器负责确定性结构，模型负责语义理解。

### 4.3 默认策略

| 文件类型 | 默认解析 | fallback |
| --- | --- | --- |
| DOCX | Docling / python-docx | 模型补充章节识别 |
| XLSX | openpyxl | Docling 表格理解 |
| PDF | Docling | MinerU / Marker |
| 扫描 PDF | Docling OCR / MinerU | 人工确认 |
| 图片 | OCR + 多模态模型 | 人工确认 |
| HTML | Readability/Markdown 转换 | Firecrawl/Crawl4AI |

## 5. RAG 与 Milvus

### 5.1 是否使用 Milvus

建议使用 Milvus。

- MVP：`Milvus Lite`，适合本地 CLI、开发测试、小规模知识库。
- 生产：`Milvus Standalone` 或 `Milvus Distributed`。
- 好处：同一套 `pymilvus` API，本地到生产迁移成本低。

### 5.2 RAG 推荐组合

```text
Document Agent
→ chunks
→ embeddings
→ Milvus Lite
→ LlamaIndex Retriever
→ 模型回答/抽取/生成
```

### 5.3 RAG 不进入第一闭环的范围

MVP 第一闭环是 Document + Product。RAG 作为 Knowledge Agent 的基础能力预留，不影响 Product Agent 开发。

## 6. 爬虫/采集定位

爬虫不是 Everida 的业务模块，而是 Agent 可调用的 MCP 工具。

### 6.1 工具职责

- 获取公开网页内容。
- 提取正文。
- 页面截图。
- 批量 URL 采集。
- 保存原始内容与元数据。

### 6.2 不做事项

- 不做平台账号自动化。
- 不绕登录、风控、验证码。
- 不做自动评论、私信、点赞、发布。
- 不将小红书/抖音/大众点评爬虫作为 MVP 强绑定功能。

### 6.3 推荐工具

| 场景 | 推荐 |
| --- | --- |
| 通用网页采集 | Crawlee Python |
| 动态页面 | Playwright |
| 网页转 Markdown | Firecrawl / Crawl4AI |
| 截图 | Playwright |

## 7. SQL 方案

### 7.1 生成

模型生成 SQL 草稿，但必须通过 schema 和规则约束。

### 7.2 校验

- `SQLGlot`：解析 AST、识别表、字段、语句类型。
- `SQLFluff`：lint 和风格检查。
- 自定义规则：禁止生产执行、检查核心表、检查产品编码、检查重复/遗漏。

### 7.3 执行策略

MVP 不提供生产库执行能力，只生成和校验 SQL 文件。

## 8. 异步任务系统

MVP 第一阶段需要完整异步任务系统，但不必一开始引入重型分布式调度。推荐实现：

- `FastAPI` 接收任务并返回 `task_id`。
- `SQLite` 或本地轻量数据库持久化任务状态、输入参数、错误信息和产物索引。
- 独立 worker 进程执行 Document/Product Agent。
- 状态机至少包含 `created`、`queued`、`running`、`completed`、`failed`、`cancelled`、`retrying`。
- API 支持任务创建、状态查询、取消、重试和产物下载。
- 后续多用户/分布式场景再迁移到 Redis/RQ/Celery、Prefect 或 Temporal。

## 9. 推荐项目结构

```text
everida/
├─ packages/
│  ├─ everida-core/
│  ├─ everida-cli/
│  ├─ everida-api/
│  └─ everida-mcp/
├─ agents/
│  ├─ document/
│  ├─ product/
│  ├─ knowledge/
│  ├─ content/
│  ├─ data/
│  └─ report/
├─ tools/
│  ├─ document_parse/
│  ├─ web_collect/
│  ├─ sql_validate/
│  └─ artifact/
├─ schemas/
├─ docs/
└─ tests/
```

## 10. 技术决策

| 决策 | 结论 |
| --- | --- |
| 第一阶段是否做 Web | 不做 |
| 第一阶段是否接平台 API | 不接 |
| 第一阶段是否做 MCP Server | 可先定义工具接口，是否实现看工期 |
| 第一阶段是否用 LangGraph | 暂不强依赖 |
| RAG 是否使用 Milvus | 是，MVP 用 Milvus Lite |
| 文档解析是否用模型 API | 用，但模型负责理解，解析和校验由代码负责 |
| 爬虫是否作为业务模块 | 否，作为 MCP 工具 |
