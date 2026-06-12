# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

TyyCode — 终端 CLI Agent，类似 Claude Code，用 Python 构建。支持多 LLM provider、工具调用、上下文管理。

## 常用命令

```bash
# 安装依赖
uv sync

# 运行（开发模式）
uv run python -m tyycode

# 运行（直接命令）
uv run tyycode

# 测试
uv run pytest
uv run pytest tests/test_agent.py  # 单个文件
uv run pytest tests/test_agent.py::test_function  # 单个测试

# 代码检查
uv run ruff check src/
uv run ruff format src/

# 类型检查
uv run mypy src/
```

## 架构要点

**核心循环**：用户输入 → REPL → Agent 主循环 → LLM 调用 → 响应解析 → (文本输出 | 工具执行 → 回传 LLM)

**模块职责**：
- `core/agent.py` — 调度中心，处理消息和工具调用
- `core/llm.py` — LLM 封装，支持流式输出、重试、多 provider 切换
- `core/context.py` — 上下文管理，token 计数 + 摘要压缩
- `core/config.py` — TOML 配置加载（`~/.tyycode/config.toml`）
- `tools/` — 工具系统，继承 `base.Tool`，通过注册表自动发现
- `ui/repl.py` — prompt_toolkit REPL 交互
- `ui/display.py` — rich 输出渲染

**工具调用格式**：OpenAI Function Calling 标准

**配置文件**：`~/.tyycode/config.toml`，支持多 provider 定义，运行时通过 `--provider` 切换

## 关键约束

- Python 3.10+，所有函数必须有类型注解
- 工具执行默认超时 30s，可在配置中调整
- 文件操作限制在项目目录内（安全沙箱）
- 危险 shell 命令（rm -rf、sudo 等）需用户确认
- LLM 调用失败自动重试 3 次（指数退避），可 fallback 到其他 provider
- 单会话 token 上限可在配置中设置（max_tokens_per_session）
- 会话自动保存到 `~/.tyycode/sessions/`

## 终端 UI 规范

- 深色科技感（VS Code Dark+ 风格）
- 启动显示紫色 ASCII art logo
- ANSI 色彩：青色=强调、绿色=成功、红色=错误、灰色=次要信息
- 代码块：左侧青色竖线 + 语法高亮
- 工具执行：spinner 动画

## 设计文档

详细规范见：
- `rules.md` — 编码规范 + 约束
- `tech-stack.md` — 技术选型 + 配置格式
- `architecture.md` — 架构设计 + UI Design Specs
- `api-docs/openapi.yaml` — 内部模块接口规范