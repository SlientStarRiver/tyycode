# rules.md

> 本文件由项目启动架构师生成，供 AI Coder 在整个开发过程中遵守。

## 项目概述
TyyCode — 一个类似 Claude Code 的终端 CLI Agent，用 Python 构建，提供交互式终端界面与 LLM 对话能力。

## 技术栈约束
- 语言：Python 3.10+（使用现代语法，type hints 必须）
- CLI 框架：typer + rich（终端美化 + 命令解析）
- LLM 调用：openai SDK（兼容 OpenAI 接口的任意 provider）
- 交互终端：prompt_toolkit（REPL 体验）
- 包管理：uv（优先）或 pip

## 代码风格
- 命名：函数/变量 snake_case，类 PascalCase，常量 UPPER_SNAKE_CASE
- 类型注解：所有函数必须有完整类型注解（参数 + 返回值）
- 注释：只写"为什么"，不写"做什么"
- 行长：88 字符（black 默认）

## 文件结构约定
```
tyycode/
├── src/
│   └── tyycode/
│       ├── __init__.py
│       ├── __main__.py        # 入口
│       ├── cli.py             # CLI 命令定义
│       ├── core/
│       │   ├── __init__.py
│       │   ├── agent.py       # Agent 主循环
│       │   ├── llm.py         # LLM 调用封装
│       │   ├── context.py     # 上下文管理
│       │   └── config.py      # 配置管理
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── base.py        # 工具基类
│       │   ├── file_ops.py    # 文件读写
│       │   ├── shell.py       # 命令执行
│       │   └── search.py      # 代码搜索
│       └── ui/
│           ├── __init__.py
│           ├── repl.py        # REPL 交互
│           └── display.py     # 输出格式化
├── tests/
├── pyproject.toml
└── README.md
```

## 命名规范
- 工具类：`tools/工具名.py`，类名 `XxxTool`
- 核心模块：`core/功能名.py`
- CLI 命令：`cli.py` 中用 typer 定义

## 终端 UI 规范
- 启动时显示 TyyCode ASCII art logo（紫色）
- 配色：深色科技感（VS Code Dark+ 风格）
- 代码块：左侧青色竖线 + 语法高亮
- 状态显示：spinner 动画 + 彩色状态文字
- 详细规范见 architecture.md → UI Design Specs

## Git 提交规范
格式：`<type>(<scope>): <subject>`
类型：feat / fix / docs / style / refactor / test / chore

## 错误处理要求
- LLM 调用：必须捕获网络异常 + API 异常，走重试逻辑
- 工具执行：必须设置超时，超时后终止进程
- 所有异常：必须向用户展示友好错误信息，禁止 raw traceback

## 禁止行为
- 禁止裸 except，必须捕获具体异常
- 禁止在工具实现中直接 print，使用 logging 或 rich console
- 禁止硬编码 API key，必须从环境变量或配置文件读取
- 禁止跳过类型注解
- 禁止无限重试，最多 3 次