# LLM Gateway

LLM Gateway 是一个基于 FastAPI 的 OpenAI-compatible 大模型网关后端。项目采用“薄核心 + 可插拔扩展”的设计：核心只负责协议接入、静态鉴权、模型别名路由、Provider Adapter、请求日志、Token 估算和基础可观测性；RAG 与 Agent Runtime 作为网关消费者存在，不在核心中实现文档切分、向量库、检索编排、工具执行或 Agent 决策循环。

当前版本是 V0.1 MVP，目标是交付一个可运行、可测试、可扩展的最小闭环。

## 功能特性

- OpenAI-compatible API：
  - `GET /healthz`
  - `GET /v1/models`
  - `POST /v1/chat/completions`
- 静态 Gateway API Key 鉴权：`Authorization: Bearer <api-key>`
- 模型别名路由：API 层只接收别名，真实 Provider 和模型由 `core/router.py` 解析
- Provider Adapter：
  - `MockProvider`：默认可用，本地无需真实大模型密钥
  - `OpenAICompatibleProvider`：可转发到 OpenAI-compatible 服务
- OpenAI-compatible 错误响应格式
- 结构化 JSON 请求日志：
  - 覆盖成功、鉴权失败、参数校验失败、`/v1/models`、stream 未实现等请求
  - 包含 `request_id`、API Key 脱敏前缀、模型别名、Provider、实际模型、状态、耗时、Token 估算和错误码
- 本地开发、Docker、pytest 和 ruff 支持

## 技术栈

- Python 3.12+
- FastAPI
- Pydantic v2
- httpx
- pytest + pytest-asyncio
- ruff

## 项目结构

```text
.
├── config/
│   ├── gateway.yaml       # 网关服务、日志和观测配置
│   ├── providers.yaml     # Provider 声明，密钥只引用环境变量名
│   └── routes.yaml        # 模型别名到 Provider/真实模型的路由
├── src/llm_gateway/
│   ├── api/               # API 接入、依赖注入、错误格式处理
│   ├── core/              # 内部 schema、模型路由、请求调度
│   ├── observability/     # 请求日志等可观测能力
│   ├── policy/            # 鉴权等治理能力
│   ├── providers/         # Provider Adapter
│   └── utils/             # 小型通用工具
├── tests/                 # 单元和 API 行为测试
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## 快速开始

### 使用 Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

服务默认监听：

```text
http://127.0.0.1:8000
```

### 本地开发运行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

export GATEWAY_API_KEYS=sk-gw-dev
export GATEWAY_CONFIG_DIR=config

uvicorn llm_gateway.main:app --reload
```

## API 示例

健康检查不需要鉴权：

```bash
curl http://127.0.0.1:8000/healthz
```

列出模型别名：

```bash
curl http://127.0.0.1:8000/v1/models \
  -H "Authorization: Bearer sk-gw-dev"
```

非流式 Chat Completion：

```bash
curl http://127.0.0.1:8000/v1/chat/completions \
  -H "Authorization: Bearer sk-gw-dev" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "chat-fast",
    "messages": [
      {"role": "user", "content": "hello"}
    ],
    "stream": false
  }'
```

示例响应：

```json
{
  "id": "req_xxx",
  "object": "chat.completion",
  "created": 0,
  "model": "chat-fast",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Mock response from mock/mock-chat: hello"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 1,
    "completion_tokens": 6,
    "total_tokens": 7
  }
}
```

当前 V0.1 不支持流式输出，`stream=true` 会返回 `not_implemented`。

## 配置说明

核心环境变量：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `GATEWAY_API_KEYS` | 空 | 逗号分隔的 Gateway 静态 API Key |
| `GATEWAY_CONFIG_DIR` | `config` | 配置文件目录 |
| `OPENAI_API_KEY` | 空 | OpenAI-compatible Provider 的真实密钥，仅在路由切到该 Provider 时需要 |

`config/providers.yaml` 中只保存 Provider 的非敏感配置。真实密钥必须通过环境变量读取，禁止写入代码、测试、配置或文档。

默认模型路由：

| 模型别名 | Provider | 实际模型 |
| --- | --- | --- |
| `chat-fast` | `mock` | `mock-chat` |
| `chat-smart` | `mock` | `mock-chat-smart` |

如需接入 OpenAI-compatible 服务，可在 `config/routes.yaml` 中把目标 Provider 改为 `openai`，并通过 `OPENAI_API_KEY` 提供密钥。

## 日志

请求日志使用 JSON 输出，logger 名称为 `llm_gateway.requests`。典型字段包括：

```json
{
  "level": "info",
  "message": "llm_request",
  "request_id": "req_xxx",
  "api_key_prefix": "sk-gw-****abcd",
  "method": "POST",
  "path": "/v1/chat/completions",
  "http_status": 200,
  "model_alias": "chat-fast",
  "provider": "mock",
  "provider_model": "mock-chat",
  "status": "success",
  "latency_ms": 12,
  "prompt_tokens": 1,
  "completion_tokens": 6,
  "total_tokens": 7,
  "token_estimated": true
}
```

API Key 只记录脱敏值，例如 `sk-gw-1234567890abcd` 会输出为 `sk-gw-****abcd`。

## 测试与代码质量

提交前建议运行：

```bash
ruff check .
pytest
```

测试覆盖当前核心行为：

- 健康检查
- API Key 鉴权
- 模型列表
- Chat Completion 成功与错误路径
- 请求日志覆盖与 API Key 脱敏

## 架构边界

LLM Gateway 的核心边界保持克制：

- API 层只做协议接入、依赖注入和错误格式处理
- 新模型入口必须先经过模型别名路由
- 新 Provider 必须继承 `BaseProvider`
- Provider 差异通过 Adapter 隔离
- 鉴权、限流、配额等治理能力放在 `policy/`
- 日志、Trace、Metrics、成本统计放在 `observability/`

V0.1 不实现以下业务：

- 文档切分、向量库管理、检索编排、重排等 RAG 业务
- Agent 决策循环、工具执行、复杂工作流
- 数据库化 API Key 管理
- 完整限流配额
- 复杂 Fallback
- 成本账单
- Web UI

后续扩展应沿着 Adapter、Router、Policy、Plugin Hook 等边界逐步添加。
