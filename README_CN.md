# AITaskRunner

基于 Web 的自动化平台，用于编排和监控 AI 编程助手（Claude Code、Codex CLI、Gemini CLI）。

[English](README.md) | [中文](README_CN.md)

## 功能特性

- **任务管理**: 支持 Markdown 格式的任务创建、编辑和追踪
- **多 CLI 支持**: 兼容 Claude Code、OpenAI Codex CLI、Google Gemini CLI
- **多项目并行执行**: 支持同时运行多个任务，可配置最大并发数
- **批量操作**: 批量删除、状态更新、一键启动所有待处理任务
- **实时监控**: 基于 WebSocket 的实时状态更新
- **会话看门狗**: CLI 意外终止时自动恢复会话
- **上下文管理**: 达到阈值时自动重启会话
- **模板系统**: 支持变量替换和国际化的可复用任务模板
- **交叉审查**: 任务完成后可使用不同的 AI CLI 自动进行代码审查
- **项目管理**: 按项目组织任务，支持一键启动终端
- **终端集成**: 原生支持 iTerm2、Kitty 和 Windows Terminal
- **国际化**: 完整支持中英文切换
- **深色模式**: 内置深色/浅色主题切换
- **跨平台**: 支持 macOS、Linux 和 Windows 系统

## 技术栈

**后端:**
- Python 3.10+
- FastAPI 0.109+
- SQLite（使用 aiosqlite 异步操作）
- WebSocket
- Pydantic 2.5+

**前端:**
- React 19
- TypeScript 5.9
- Vite 7
- Tailwind CSS 4
- Radix UI
- Zustand 5
- i18next

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- 支持的 AI CLI 工具之一：
  - [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
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

然后在浏览器中打开 http://localhost:3000

### 5 分钟上手教程

按照以下步骤运行你的第一个自动化任务：

**第一步：配置设置**

1. 打开 http://localhost:3000，进入 **设置** 页面
2. 选择你的 **CLI 类型**（如 Claude Code）
3. 选择你的 **终端**（macOS 上的 iTerm2，Linux 上的 Kitty）
4. 设置 **最大并发会话数**（默认：3）
5. 可选开启 **交叉审查** 进行自动代码审查

**第二步：创建项目**

1. 进入 **项目** 页面
2. 点击 **新建项目**
3. 输入项目名称并选择项目目录路径
4. 使用 **启动终端** 按钮可快速打开项目目录

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
- 使用 **批量启动** 一键启动所有待处理任务
- **会话看门狗** 会自动恢复意外终止的会话

## 项目结构

```
AITaskRunner/
├── backend/                    # FastAPI 后端
│   ├── app.py                 # 主应用程序和 API 路由
│   ├── database/              # 数据库模型（SQLite）
│   │   ├── models.py          # SQLAlchemy 模型
│   │   └── shared.py          # 共享数据库连接池
│   ├── models/                # Pydantic 模型
│   │   └── schemas.py         # 请求/响应模型
│   ├── services/              # 业务逻辑
│   │   ├── codex_service.py   # CLI 会话管理
│   │   ├── task_service_db.py # 任务 CRUD 操作
│   │   ├── template_service.py# 模板管理
│   │   ├── settings_service.py# 设置管理
│   │   └── project_service.py # 项目管理
│   ├── utils/                 # 工具函数
│   │   └── markdown_checker.py# 任务进度检测
│   └── tests/                 # 后端单元测试
├── frontend/                   # React 前端
│   └── src/
│       ├── pages/             # 页面组件
│       │   ├── Tasks.tsx      # 任务管理
│       │   ├── Sessions.tsx   # 会话监控
│       │   ├── Projects.tsx   # 项目管理
│       │   ├── Templates.tsx  # 模板编辑器
│       │   ├── Settings.tsx   # 系统设置
│       │   └── Logs.tsx       # 日志查看器
│       ├── components/        # 可复用组件
│       ├── stores/            # Zustand 状态管理
│       ├── api/               # API 客户端
│       ├── i18n/              # 国际化
│       └── types/             # TypeScript 类型
├── core/                       # 核心监控逻辑
│   ├── cli_adapters/          # CLI 工具适配器
│   │   ├── base.py            # 基础适配器接口
│   │   ├── claude_code.py     # Claude Code 适配器
│   │   ├── codex.py           # Codex CLI 适配器
│   │   └── gemini.py          # Gemini CLI 适配器
│   ├── terminal_adapters/     # 终端适配器
│   │   ├── base.py            # 基础终端接口
│   │   ├── iterm.py           # iTerm2 适配器 (macOS)
│   │   ├── kitty.py           # Kitty 适配器 (macOS/Linux)
│   │   └── windows_terminal.py# Windows Terminal 适配器
│   ├── session/               # 会话池管理
│   │   ├── manager.py         # 会话管理器
│   │   ├── models.py          # 会话模型
│   │   └── watchdog.py        # 会话看门狗
│   ├── cli_monitor.py         # CLI 监控器
│   ├── context_manager.py     # 上下文追踪
│   └── task_manager.py        # 任务执行管理器
├── e2e/                        # 端到端测试 (Playwright)
└── start_web.py               # 应用程序入口
```

## 配置

可通过 Web UI 设置页面进行配置：

| 设置项 | 说明 | 选项 |
|--------|------|------|
| CLI 类型 | 主要使用的 AI CLI | Claude Code, Codex, Gemini |
| 审查 CLI | 交叉审查使用的 CLI | Claude Code, Codex, Gemini |
| 终端 | 终端模拟器 | 自动, iTerm2, Kitty, Windows Terminal |
| 最大并发会话数 | 并行任务数量限制 | 1-10 |
| 审查模式 | 启用交叉审查 | 开/关 |
| 看门狗 | 自动恢复会话 | 开/关 |
| 语言 | 界面语言 | 英文, 中文 |

## 支持的终端

| 终端             | macOS | Linux | Windows |
|------------------|-------|-------|---------|
| Windows Terminal | -     | -     | 是      |
| iTerm2           | 是    | -     | -       |
| Kitty            | 是    | 是    | -       |

**注意：** Kitty 终端支持高级功能，如空闲检测以实现自动会话恢复。

## API 参考

后端在 `http://localhost:8086` 提供 REST API：

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/init` | GET | 获取所有初始化数据（任务、会话、项目、设置） |
| `/api/tasks` | GET/POST | 列表/创建任务 |
| `/api/tasks/{id}` | GET/PUT/DELETE | 获取/更新/删除任务 |
| `/api/tasks/{id}/start` | POST | 启动任务会话 |
| `/api/tasks/{id}/notify-status` | POST | CLI 回调接口 |
| `/api/tasks/batch/start` | POST | 批量启动所有待处理任务 |
| `/api/tasks/batch/delete` | POST | 批量删除任务 |
| `/api/tasks/batch/status` | POST | 批量更新状态 |
| `/api/sessions` | GET | 获取所有会话 |
| `/api/projects` | GET/POST | 列表/创建项目 |
| `/api/projects/{id}/launch` | POST | 启动项目终端 |
| `/api/templates` | GET/POST | 列表/创建模板 |
| `/api/settings` | GET | 获取所有设置 |
| `/api/settings/{key}` | GET/PUT | 获取/更新设置 |
| `/ws/monitor` | WebSocket | 实时状态更新 |

## 常见问题

### 回调/通知连接问题

- 回调地址默认使用 `http://127.0.0.1:8086`。若修改端口，请同时在 `.env` 文件中更新 `API_BASE_URL`。
- 如果本机启用了代理/安全软件阻止本地回环，回调可能失败。请确保 `127.0.0.1:8086` 可以被本机访问。
- 启动后可用 `curl http://127.0.0.1:8086/health` 自检连接状态。

### 会话无法启动

- 检查所选 CLI 工具是否已安装并在 PATH 中可访问
- 验证终端模拟器是否已安装（iTerm2、Kitty 或 Windows Terminal）
- 查看任务日志获取详细错误信息

### 会话看门狗

如果会话意外终止后未能恢复：
- 在设置中启用看门狗
- 检查终端窗口是否被手动关闭
- 查看后端日志中的看门狗消息

## 测试

```bash
# 后端单元测试
cd backend
pytest

# 前端单元测试
cd frontend
npm run test

# 端到端测试（需要运行后端）
npm run e2e
```

## 许可证

MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。
