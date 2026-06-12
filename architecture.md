# architecture.md

> 本文件由项目启动架构师生成，描述系统架构、模块职责和关键设计决策。

## 项目目录结构

```
tyycode/
├── src/
│   └── tyycode/
│       ├── __init__.py
│       ├── __main__.py        # python -m tyycode 入口
│       ├── cli.py             # typer 命令定义
│       ├── core/
│       │   ├── __init__.py
│       │   ├── agent.py       # Agent 主循环（消息处理、工具调度）
│       │   ├── llm.py         # LLM 调用封装（流式输出、重试）
│       │   ├── context.py     # 上下文管理（历史、token 计数、截断）
│       │   └── config.py      # 配置管理（pydantic-settings）
│       ├── tools/
│       │   ├── __init__.py    # 工具注册表
│       │   ├── base.py        # Tool 抽象基类
│       │   ├── file_ops.py    # 读文件、写文件、列目录
│       │   ├── shell.py       # 执行 shell 命令
│       │   └── search.py      # grep/ripgrep 代码搜索
│       └── ui/
│           ├── __init__.py
│           ├── repl.py        # REPL 主循环（prompt_toolkit）
│           └── display.py     # 输出渲染（rich）
├── tests/
│   ├── test_agent.py
│   ├── test_tools.py
│   └── test_context.py
├── pyproject.toml
└── .env.example
```

## 模块职责说明

| 模块/目录 | 职责 | 备注 |
|-----------|------|------|
| `cli.py` | CLI 入口，解析命令行参数 | typer 定义子命令 |
| `core/agent.py` | Agent 主循环：接收用户输入 → 调用 LLM → 解析工具调用 → 执行 → 返回结果 | 核心调度器 |
| `core/llm.py` | LLM API 调用封装，支持流式输出、重试、多 provider 切换 | 运行时根据配置选择 provider |
| `core/context.py` | 对话上下文管理：历史记录、token 计数、上下文截断策略 | 防止超 token 限制 |
| `core/config.py` | 配置加载：TOML 配置文件 + 环境变量 | tomli 解析 + pydantic 验证，支持多 provider |
| `tools/base.py` | Tool 抽象基类，定义工具接口（name, description, execute） | 所有工具继承 |
| `tools/file_ops.py` | 文件操作工具：read_file, write_file, list_directory | 安全沙箱限制路径 |
| `tools/shell.py` | Shell 命令执行：subprocess 封装，超时控制 | 危险命令确认 |
| `tools/search.py` | 代码搜索：grep/ripgrep 集成 | 支持正则、文件过滤 |
| `ui/repl.py` | REPL 交互循环：prompt_toolkit 构建输入界面 | 自动补全、历史 |
| `ui/display.py` | 输出渲染：代码高亮、表格、diff 显示 | rich 封装 |

## 核心数据流

```
用户输入
    ↓
REPL (ui/repl.py)
    ↓
Agent 主循环 (core/agent.py)
    ↓
上下文组装 (core/context.py)
    ↓
LLM 调用 (core/llm.py)
    ↓
响应解析
    ├─ 文本回复 → 渲染输出 (ui/display.py)
    └─ 工具调用 → 工具执行 (tools/*.py)
                    ↓
                执行结果
                    ↓
                回传 LLM（继续对话）
```

## 关键设计决策

1. **工具注册机制**：所有工具继承 `Tool` 基类，通过 `__init__.py` 中的注册表自动发现。新增工具只需创建文件 + 注册，无需改 agent 代码。

2. **上下文截断策略**：当 token 接近上限时，优先保留 system prompt + 最近 N 轮对话，中间历史用摘要替代。避免简单截断丢失关键信息。

3. **流式输出**：LLM 响应使用 streaming 模式，逐 token 输出到终端，提升用户体验（避免长时间等待）。

4. **安全沙箱**：文件操作工具限制在项目目录内，shell 命令执行前检查危险模式（rm -rf、sudo 等），需用户确认。

5. **多 provider 配置**：配置文件支持多个 provider 定义（名称 + base_url + api_key + model），运行时通过 `--provider` 参数或配置中的 `default_provider` 选择。支持 OpenAI / Ollama / DeepSeek / vLLM 等任意兼容接口。

6. **错误恢复机制**：LLM 调用失败时：
   - 网络超时：自动重试 3 次，指数退避（1s → 2s → 4s）
   - API 限流（429）：等待 Retry-After 头指定时间后重试
   - Provider 故障：自动 fallback 到配置中的下一个 provider
   - 所有重试失败：向用户展示错误信息，允许手动切换 provider

7. **Token 预算控制**：
   - 配置文件支持 `max_tokens_per_session`（单会话 token 上限）
   - 接近上限时警告，超过上限时拒绝继续（需用户确认或结束会话）
   - 每次 LLM 调用后累加 token 用量，实时显示消耗

8. **工具执行超时**：
   - 默认超时：30 秒
   - 配置文件支持 `tool_timeout` 参数自定义
   - 超时后自动终止进程，返回超时错误
   - 长时间命令（如 build）可单独标记 `timeout: 300`

9. **会话持久化**：
   - 会话自动保存到 `~/.tyycode/sessions/{session_id}.json`
   - 包含：对话历史、token 用量、使用的时间
   - 支持 `--resume` 参数恢复历史会话
   - 会话列表：`tyycode sessions` 命令查看所有历史会话

## 外部依赖与集成点

| 服务 | 用途 | 接入方式 |
|------|------|----------|
| OpenAI API | LLM 推理（默认） | openai SDK，API Key 认证 |
| Ollama | 本地 LLM 推理 | openai SDK，base_url 指向 localhost:11434 |
| DeepSeek / vLLM 等 | 备选 LLM 推理 | openai SDK，自定义 base_url |
| ripgrep（可选）| 高速代码搜索 | subprocess 调用 rg 命令 |

## 开发注意事项
- UI 实现必须以 **prototype/index.html** 为唯一视觉依据（如有）
- 设计规范以 **architecture.md → UI Design Specs** 段落为准（如有）
- 设计稿/Specs 存在缺失或歧义时，必须暂停并向用户确认

## UI Design Specs
> 由 Phase 3.5 定稿后回写。终端 CLI 工具的视觉规范。
> 来源：用户指定（深色科技感 + 启动 ASCII art）

### 设计风格
- 深色科技感，类似 VS Code Dark+ 主题
- 启动时显示大字 ASCII art logo
- 代码高亮使用深色背景 + 亮色前景

### 色彩规范（ANSI 颜色码）
| 用途 | ANSI 码 | 说明 |
|------|---------|------|
| 背景 | 默认终端背景 | 透明，使用终端自身背景 |
| 正文 | \033[37m (白色) | 主要文字 |
| 强调 | \033[36m (青色) | 重点信息、选中项 |
| 成功 | \033[32m (绿色) | 成功状态、工具执行完成 |
| 警告 | \033[33m (黄色) | 警告信息 |
| 错误 | \033[31m (红色) | 错误信息 |
| 次要 | \033[90m (灰色) | 时间戳、路径等次要信息 |
| Logo | \033[35m (紫色) | TyyCode ASCII art |
| 代码块 | \033[33m (黄色) | 代码高亮关键字 |

### 启动 ASCII Art
```
  ████████╗██╗   ██╗██╗   ██╗ ██████╗ ██████╗ ██████╗ ███████╗
  ╚══██╔══╝╚██╗ ██╔╝╚██╗ ██╔╝██╔════╝██╔═══██╗██╔══██╗██╔════╝
     ██║    ╚████╔╝  ╚████╔╝ ██║     ██║   ██║██║  ██║█████╗
     ██║     ╚██╔╝    ╚██╔╝  ██║     ██║   ██║██║  ██║██╔══╝
     ██║      ██║      ██║   ╚██████╗╚██████╔╝██████╔╝███████╗
     ╚═╝      ╚═╝      ╚═╝    ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝
```
- 使用紫色（\033[35m）显示
- 启动后显示版本号 + 当前 provider 信息

### 终端组件样式
- **输入提示符**：`❯ `（青色）或 `tyycode ❯ `
- **工具执行中**：spinner（⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏ 循环）+ 工具名
- **代码块**：左侧竖线（青色）+ 语法高亮
- **表格**：使用 rich 的深色主题表格
- **分隔线**：灰色虚线 `────────────────────`

### 交互模式
- 工具执行：spinner 动画 + 实时输出
- 错误：红色背景高亮错误行
- 多轮对话：用空行分隔不同轮次
- Tab 补全：弹出菜单，青色高亮选中项

### 原型文件
- 终端工具无需 HTML 原型
- 设计规范直接在代码中实现