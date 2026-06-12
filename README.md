# TyyCode

Terminal CLI Agent - 类似 Claude Code 的终端助手，用 Python 构建。

## 安装

```bash
pip install tyycode
```

或从源码安装：

```bash
git clone https://github.com/SlientStarRiver/tyycode.git
cd tyycode
pip install -e .
```

## 使用

```bash
tyy              # 启动交互模式
tyy run "你好"   # 单次执行
tyy sessions     # 查看历史会话
```

## 配置

创建配置文件 `~/.tyycode/config.toml`：

```toml
default_provider = "deepseek"
max_tokens_per_session = 100000
tool_timeout = 30

[[providers]]
name = "deepseek"
base_url = "https://api.deepseek.com/v1"
api_key = "sk-xxx"
model = "deepseek-chat"
```

支持的 Provider：OpenAI / DeepSeek / Ollama / 任意 OpenAI 兼容接口。

## 功能

- 多 LLM Provider 支持
- 工具调用：文件读写、Shell 命令、代码搜索
- 上下文管理 + 摘要压缩
- 会话持久化
- REPL 自动补全 + 历史记录
- 终端 UI：ASCII art logo + 语法高亮

## 开发

```bash
pip install -e ".[dev]"
pytest                # 运行测试
ruff check src/       # 代码检查
```

## License

MIT
