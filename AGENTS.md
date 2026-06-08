# AGENTS.md

本仓库是 LLM Gateway 的 Python 后端工程。后续 Codex 或其他自动化开发者必须遵守以下规范。

## 架构边界

- 总原则是“薄核心 + 可插拔扩展”。
- 核心层只负责统一协议、鉴权、静态/动态路由、Provider Adapter、请求日志、Token/成本统计和基础可观测性。
- RAG 是 Gateway 的消费者，不在核心里实现文档切分、向量库管理、检索编排或重排业务。
- Agent Runtime 是 Gateway 的消费者，不在核心里实现 Agent 决策循环、工具执行或复杂工作流。
- V0.1 不创建 RAG/Agent 业务实现；后续如需脚手架，只能放接口、钩子和轻量占位，复杂业务应独立服务化。

## 技术约束

- Python 版本为 3.12+。
- Web 框架使用 FastAPI。
- 数据校验使用 Pydantic v2。
- 外部 HTTP 调用使用 httpx。
- 测试使用 pytest + pytest-asyncio。
- 代码质量使用 ruff。
- 包管理和依赖声明以 `pyproject.toml` 为准。
- 不引入过重依赖；新增依赖前必须说明必要性。
- 禁止实现 Web UI，除非有明确需求。
- 禁止把任何真实 API Key、Token、密码写入代码、测试、配置或文档。

## 代码组织

- 使用 src-layout，业务包位于 `src/llm_gateway`。
- API 层放在 `api/`，只做协议接入、依赖注入和错误格式处理。
- 统一内部 schema 放在 `core/schemas.py`。
- 模型路由与调度放在 `core/`。
- Provider Adapter 放在 `providers/`，每个 Provider 一个独立实现。
- 鉴权、限流、配额等治理能力放在 `policy/`。
- 日志、Trace、Metrics、成本统计放在 `observability/`。
- 小型通用工具放在 `utils/`。

## 开发要求

- 优先保持 OpenAI-compatible，对外响应和错误格式不得随意破坏兼容。
- 新 Provider 必须继承 `BaseProvider`，并通过 `main.py` 的 Provider 加载逻辑装配。
- 新模型入口必须先经过模型别名路由，不允许 API 层直接调用 Provider。
- 路由策略必须通过 `core/router.py` 实现。
- Provider 差异必须通过 Adapter 隔离。
- 鉴权、限流、成本、日志等横切能力放在 `policy/` 或 `observability/` 中。
- 请求日志至少保留 `request_id`、`api_key_prefix`、模型别名、Provider、实际模型、状态、耗时、Token 估算和错误信息。
- 配置文件只放结构化非敏感配置；密钥只能通过环境变量读取。
- 新增核心行为必须补测试。
- 提交前运行 `ruff check .` 和 `pytest`。

## V0.1 范围提醒

当前版本只交付最小可用闭环。不要提前实现数据库管理 API Key、完整限流配额、复杂 Fallback、成本账单、RAG 业务或 Agent Runtime。后续扩展应沿着 Adapter、Router、Policy、Plugin Hook 这些边界逐步添加。
