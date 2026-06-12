# tech-stack.md

> 本文件由项目启动架构师生成，记录项目技术选型及配置基准。

## 核心技术栈

| 层级 | 技术 | 版本 | 用途 | 选用理由 |
|------|------|------|------|----------|
| 语言 | Python | 3.10+ | 主语言 | 生态成熟，AI/LLM 库丰富，开发效率高 |
| CLI 框架 | typer | 0.9+ | 命令行解析 | 基于 click，类型注解驱动，自动生成 help |
| 终端美化 | rich | 13+ | 输出格式化 | 语法高亮、表格、进度条，开箱即用 |
| 交互终端 | prompt_toolkit | 3.0+ | REPL 体验 | 自动补全、历史记录、多行编辑 |
| LLM SDK | openai | 1.0+ | API 调用 | 兼容 OpenAI 接口，支持任意 provider |
| 配置管理 | tomli + pydantic | 2.0+ | TOML 配置解析 | Python 3.11+ 用 tomllib，低版本用 tomli |
| 测试 | pytest | 7+ | 单元测试 | fixtures 灵活，插件生态丰富 |
| 包管理 | uv | 0.1+ | 依赖管理 | 比 pip 快 10-100x，兼容 pip 生态 |

## 开发环境要求
- Python：>= 3.10
- uv：>= 0.1.0（推荐）或 pip
- 操作系统：macOS / Linux / Windows (WSL)

## 关键依赖说明
- `openai`：不仅支持 OpenAI，还支持任何兼容接口（Ollama、vLLM、DeepSeek 等）
- `prompt_toolkit`：比 input() 强大得多，支持语法高亮、多行编辑、自动补全
- `tomli`：TOML 解析（Python 3.11+ 用内置 `tomllib`，低版本用 `tomli`）
- `pydantic`：配置模型定义，类型验证 + 默认值

## 配置文件说明
```toml
# ~/.tyycode/config.toml

default_provider = "openai"

[[providers]]
name = "openai"
base_url = "https://api.openai.com/v1"
api_key = "sk-xxx"
model = "gpt-4o"

[[providers]]
name = "ollama"
base_url = "http://localhost:11434/v1"
api_key = "ollama"
model = "qwen2.5-coder:7b"
```

## 配置文件完整示例
```toml
# ~/.tyycode/config.toml

default_provider = "openai"

# Token 预算
max_tokens_per_session = 100000  # 单会话 token 上限

# 工具执行超时（秒）
tool_timeout = 30

[[providers]]
name = "openai"
base_url = "https://api.openai.com/v1"
api_key = "sk-xxx"
model = "gpt-4o"

[[providers]]
name = "ollama"
base_url = "http://localhost:11434/v1"
api_key = "ollama"
model = "qwen2.5-coder:7b"
```

## 环境变量（可选，优先级低于配置文件）
```env
TYYCODE_CONFIG_PATH=            # 配置文件路径（默认 ~/.tyycode/config.toml）
```

## 初始化命令
```bash
# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 初始化项目
uv init tyycode
cd tyycode
uv add openai rich typer prompt-toolkit tomli pydantic

# 开发模式
uv run python -m tyycode

# 测试
uv run pytest
```

## 后端服务说明
无后端服务。TyyCode 是纯本地 CLI 工具，直接调用 LLM API provider（OpenAI / Ollama / 其他兼容接口）。