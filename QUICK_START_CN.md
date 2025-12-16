# 快速开始指南

[English](QUICK_START_EN.md) | [中文](QUICK_START.md)

## 5分钟快速上手

### 步骤 1: 安装依赖

**后端依赖：**
```bash
pip install -r backend/requirements.txt
```

**前端依赖：**
```bash
cd frontend
npm install
cd ..
```

### 步骤 2: 启动服务

**启动后端：**
```bash
python start_web.py
```

**启动前端（新终端）：**
```bash
cd frontend
npm run dev
```

### 步骤 3: 访问系统

打开浏览器访问: `http://localhost:3500`

## 创建第一个任务

### 方法 1: 使用 Web 界面

1. 进入 **设置** 页面，配置：
   - CLI 类型（Claude Code / Codex / Gemini）
   - 终端类型（iTerm2 / Kitty / Windows Terminal）
   - 最大并发会话数

2. 进入 **项目** 页面，创建新项目：
   - 填写项目名称
   - 选择项目目录路径
   - 可使用 **启动终端** 快速打开项目目录

3. 进入 **任务** 页面，创建任务：
   - 填写任务标题
   - 选择关联项目
   - 指定 Markdown 文档路径
   - 点击 **保存** 后点击 **启动**

### 方法 2: 使用 API

```python
import requests

# 创建任务
response = requests.post('http://localhost:8086/api/tasks', json={
    "title": "我的第一个任务",
    "project_directory": "/path/to/my_project",
    "markdown_document_path": "/path/to/my_project/tasks/task.md"
})
task = response.json()

# 启动任务
requests.post(f'http://localhost:8086/api/tasks/{task["id"]}/start')
```

## Markdown 文档格式

任务文档使用 Markdown 格式，系统会自动识别复选框并跟踪进度：

```markdown
# 项目标题

## 项目概述
简要描述项目的目标和背景

## 技术栈
- **编程语言**: Python
- **框架**: FastAPI
- **数据库**: PostgreSQL

## 任务清单

### 1. 项目初始化
- [ ] 创建项目目录结构
- [ ] 配置开发环境
- [ ] 初始化 Git 仓库

### 2. 核心功能开发
- [ ] 实现用户认证
- [ ] 开发 API 接口
- [ ] 数据库设计

### 3. 测试和部署
- [ ] 编写单元测试
- [ ] 配置 CI/CD
- [ ] 部署到生产环境

## 实现说明
详细的实现要求和注意事项...
```

**注意：** 使用 `- [ ]` 格式的复选框，系统会自动检测任务完成状态。

## 常用操作

### 批量操作

任务页面支持批量操作：
- **批量启动**：一键启动所有待处理任务
- **批量删除**：选中多个任务后删除
- **批量修改状态**：批量设置任务状态

### 项目终端

在项目页面可以：
- **启动终端**：在项目目录打开终端
- **启动 CLI**：直接启动 AI CLI 工具
- **危险模式**：启动带自动确认参数的 CLI

### 查看日志

任务执行过程中的所有日志可以在：
- 任务详情页面查看
- 日志页面查看所有任务日志

## 核心功能

### 会话看门狗

自动检测并恢复意外终止的会话：
- 终端窗口意外关闭时自动重启
- Kitty 终端支持 CLI 空闲检测
- 在设置页面可开启/关闭

### Cross-Review

使用不同的 AI CLI 进行交叉审查：
- 任务完成后自动切换到审查 CLI
- 支持任务级别和全局级别开关
- 在设置页面配置审查 CLI 类型

### 上下文管理

当 CLI 上下文达到阈值时：
- 自动重启会话继续执行
- 使用 `resume_task` 模板恢复进度
- 无需人工干预

## 常见问题

### Q1: 后端启动失败？

检查端口是否被占用：
```bash
lsof -i :8086
```

确保 Python 3.10+ 已安装：
```bash
python --version
```

### Q2: 前端无法连接后端？

确保后端服务已启动，检查 `.env` 文件中的 `API_BASE_URL` 配置。

### Q3: CLI 会话无法启动？

1. 确认已安装所选的 CLI 工具（claude / codex / gemini）
2. 确认终端模拟器已安装（iTerm2 / Kitty）
3. 查看任务日志获取详细错误信息

### Q4: 任务进度不更新？

1. 确保 Markdown 文档使用正确的复选框格式 `- [ ]`
2. 检查回调 URL 是否正确配置
3. 运行 `curl http://127.0.0.1:8086/health` 测试连接

### Q5: 如何查看更多日志？

后端日志直接输出到启动 `start_web.py` 的终端。

## API 快速参考

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/init` | GET | 获取初始化数据 |
| `/api/tasks` | GET/POST | 列表/创建任务 |
| `/api/tasks/{id}/start` | POST | 启动任务 |
| `/api/tasks/batch/start` | POST | 批量启动 |
| `/api/sessions` | GET | 获取会话列表 |
| `/api/projects` | GET/POST | 列表/创建项目 |
| `/api/projects/{id}/launch` | POST | 启动项目终端 |
| `/api/settings` | GET | 获取设置 |
| `/ws/monitor` | WebSocket | 实时状态推送 |

## 更多资源

- [完整文档](README.md)
- [API 文档](http://localhost:8086/docs) - 启动后端后访问

---

**提示**: 建议先用小型测试项目熟悉系统，再用于实际开发任务。
