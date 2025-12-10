# AITaskRunner

基于 Web 的自动化平台，用于编排和监控 AI 编程助手（Claude Code、Codex CLI、Gemini CLI）。

[English](README.md) | [中文](README_CN.md)

## 功能特性

- **任务管理**: 支持 Markdown 格式的任务创建、编辑和追踪
- **多 CLI 支持**: 兼容 Claude Code、OpenAI Codex CLI、Google Gemini CLI
- **多项目并行执行**: 支持同时运行多个任务，可配置最大并发数
- **实时监控**: 基于 WebSocket 的实时状态更新
- **上下文管理**: 达到阈值时自动重启会话
- **模板系统**: 支持变量替换和国际化的可复用任务模板
- **交叉审查**: 任务完成后可使用不同的 AI CLI 自动进行代码审查
- **项目管理**: 按项目组织任务
- **终端集成**: 原生支持 iTerm2、Kitty 和 Windows Terminal
- **国际化**: 完整支持中英文切换
- **深色模式**: 内置深色/浅色主题切换
- **跨平台**: 支持 macOS 和 Windows 系统

## 技术栈

**后端:**
- Python 3.10+
- FastAPI
- SQLite（使用 aiosqlite 异步操作）
- WebSocket

**前端:**
- React 19
- TypeScript
- Vite
- Tailwind CSS
- Radix UI
- Zustand
- i18next

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- 支持的 AI CLI 工具之一：
  - [Claude Code](https://github.com/anthropics/claude-code)
  - [Codex CLI](https://github.com/openai/codex)
  - [Gemini CLI](https://github.com/google-gemini/gemini-cli)

### 安装

1. 克隆仓库

```bash
git clone https://github.com/yourusername/AITaskRunner.git
cd AITaskRunner
```

2. 安装后端依赖

```bash
pip install -r backend/requirements.txt
```

3. 安装前端依赖

```bash
cd frontend
npm install
cd ..
```

### 运行

**开发模式:**

```bash
# 终端 1 - 后端
python start_web.py

# 终端 2 - 前端
cd frontend
npm run dev
```

**或使用启动脚本:**

```bash
python start_web.py
```

然后在浏览器中打开 http://localhost:3000

### 5 分钟上手教程

按照以下步骤运行你的第一个自动化任务：

**第一步：配置设置**

1. 打开 http://localhost:3000，进入 **设置** 页面
2. 选择你的 **CLI 类型**（如 Claude Code）
3. 选择你的 **终端**（如 macOS 上的 iTerm2）
4. 设置 **最大并发会话数**（默认：3）

**第二步：创建项目**

1. 进入 **项目** 页面
2. 点击 **新建项目**
3. 输入项目名称并选择项目目录路径

**第三步：创建任务文档**

在你的项目目录中创建一个 markdown 文件（如 `tasks/feature-login.md`）：

```markdown
# 实现用户登录功能

## 任务列表

- [ ] 创建包含邮箱和密码字段的登录表单组件
- [ ] 添加表单验证（邮箱格式、密码长度）
- [ ] 实现登录 API 调用
- [ ] 处理登录成功/失败状态
- [ ] 添加"记住我"复选框功能
```

**第四步：创建并启动任务**

1. 进入 **任务** 页面
2. 点击 **新建任务**
3. 填写：
   - **标题**：实现用户登录
   - **项目**：选择你的项目
   - **文档路径**：你的 markdown 文件路径
4. 点击 **保存**，然后点击 **启动**

**第五步：监控进度**

- 系统会打开一个运行 AI CLI 的终端窗口
- 在 **会话** 页面实时查看进度
- 查看任务日志了解详细执行历史
- AI 会自动在你的 markdown 文件中勾选已完成的项目

**小贴士：**

- 在 markdown 中使用复选框格式（`- [ ]`）来创建可追踪的子任务
- 系统会在达到上下文限制时自动重启会话
- 启用 **交叉审查** 让不同的 AI 审查已完成的工作
- 可以在不同项目中并行运行多个任务

## 项目结构

```
AITaskRunner/
├── backend/                    # FastAPI 后端
│   ├── app.py                 # 主应用程序和 API 路由
│   ├── database/              # 数据库模型（SQLite）
│   ├── models/                # Pydantic 模型
│   ├── services/              # 业务逻辑
│   │   ├── codex_service.py   # CLI 会话管理
│   │   ├── task_service_db.py # 任务 CRUD 操作
│   │   ├── template_service.py# 模板管理
│   │   ├── settings_service.py# 设置管理
│   │   └── project_service.py # 项目管理
│   └── utils/                 # 工具函数
├── frontend/                   # React 前端
│   └── src/
│       ├── pages/             # 页面组件
│       ├── components/        # 可复用组件
│       ├── stores/            # Zustand 状态管理
│       ├── api/               # API 客户端
│       ├── i18n/              # 国际化
│       └── types/             # TypeScript 类型
├── core/                       # 核心监控逻辑
│   ├── cli_adapters/          # CLI 工具适配器
│   │   ├── claude_code.py     # Claude Code 适配器
│   │   ├── codex.py           # Codex CLI 适配器
│   │   └── gemini.py          # Gemini CLI 适配器
│   ├── terminal_adapters/     # 终端适配器
│   │   ├── iterm.py           # iTerm2 适配器
│   │   ├── kitty.py           # Kitty 适配器
│   │   └── windows_terminal.py# Windows Terminal 适配器
│   ├── session/               # 会话池管理
│   ├── cli_monitor.py         # CLI 监控器
│   └── context_manager.py     # 上下文追踪
```

## 配置

可通过 Web UI 设置页面进行配置：

- **CLI 类型**: 选择使用的 AI CLI（Claude Code、Codex、Gemini）
- **终端**: 选择终端模拟器（iTerm2、Kitty、Windows Terminal）
- **最大并发会话数**: 限制并行任务执行数量（1-10）
- **审查模式**: 启用/禁用使用不同 CLI 进行交叉审查
- **语言**: 切换中英文界面

## 支持的终端

| 终端             | macOS | Linux | Windows |
|------------------|-------|-------|---------|
| Windows Terminal | -     | -     | 是      |
| iTerm2           | 是    | -     | -       |
| Kitty            | 是    | 是    | -       |

系统会自动检测并使用您平台上最佳的可用终端。

## 常见问题

### 回调/通知连接问题

- 回调地址默认使用 `http://127.0.0.1:8086`（由 `start_web.py` 启动）。若修改端口，请同时在 `.env` 或设置页更新 `API_BASE_URL`。
- 如果本机启用了代理/安全软件阻止本地回环，回调可能失败。请确保 `127.0.0.1:8086` 可以被本机访问。
- 在受限环境（如沙箱、无本地网络权限）运行时，对回环的请求可能被拦截，此时需要授予本地网络访问权限或在允许网络的环境中运行后端。
- 启动后可用 `curl http://127.0.0.1:8086/health` 自检；如果失败，请检查端口占用、防火墙或重启 `start_web.py`。

## 贡献

欢迎贡献代码！请随时提交 Pull Request。

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 发起 Pull Request

## 许可证

MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。
