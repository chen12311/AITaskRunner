# 快速开始指南 - 简化版任务系统

## 🚀 5分钟快速上手

### 步骤 1: 迁移数据库（如果有旧数据）

```bash
cd /Users/mac/Documents/python/zidonghua/codex_automation
python3 backend/database/migrate_to_v2.py
```

如果是全新安装，跳过此步骤。

### 步骤 2: 安装前端依赖

```bash
cd frontend
npm install
```

### 步骤 3: 启动服务

**启动后端:**
```bash
cd /Users/mac/Documents/python/zidonghua/codex_automation
python3 start_web.py
```

**启动前端（新终端）:**
```bash
cd /Users/mac/Documents/python/zidonghua/codex_automation/frontend
npm run dev
```

### 步骤 4: 访问系统

打开浏览器访问: `http://localhost:3000`

## 📝 创建第一个任务

### 方法 1: 使用 Web 界面

1. 点击"创建任务"按钮
2. 填写项目目录，例如：`/Users/username/my_project`
3. 点击"使用模板"或手动编写 Markdown 文档：

```markdown
# 我的第一个项目

## 项目概述
这是一个测试项目

## 任务清单
- [ ] 创建项目结构
- [ ] 编写代码
- [ ] 测试
```

4. 点击"创建任务"

### 方法 2: 使用 API

```python
import requests

response = requests.post('http://localhost:8000/api/tasks', json={
    "project_directory": "/Users/username/my_project",
    "markdown_document": """
# 我的第一个项目

## 项目概述
这是一个测试项目

## 任务清单
- [ ] 创建项目结构
- [ ] 编写代码
- [ ] 测试
"""
})

print(response.json())
```

### 方法 3: 使用 Python 脚本

```python
from backend.services.task_service_db import TaskServiceDB
from backend.models.schemas import TaskCreateRequest

# 创建服务
service = TaskServiceDB()

# 创建任务
task = service.create_task(TaskCreateRequest(
    project_directory="/Users/username/my_project",
    markdown_document="""
# 我的第一个项目

## 项目概述
这是一个测试项目

## 任务清单
- [ ] 创建项目结构
- [ ] 编写代码
- [ ] 测试
"""
))

print(f"任务创建成功: {task.id}")
```

## 🎯 常用操作

### 查看所有任务

**Web 界面:** 访问任务列表页面

**API:**
```python
import requests
tasks = requests.get('http://localhost:8000/api/tasks').json()
```

### 启动任务

**Web 界面:** 点击任务行的"启动"按钮

**API:**
```python
import requests
requests.post(f'http://localhost:8000/api/tasks/{task_id}/start')
```

### 查看任务详情

**Web 界面:** 点击任务行的"查看"按钮

**API:**
```python
import requests
task = requests.get(f'http://localhost:8000/api/tasks/{task_id}').json()
print(task['markdown_document'])
print(task['logs'])
```

## 📖 Markdown 文档建议格式

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
- [ ] 初始化Git仓库

### 2. 核心功能开发
- [ ] 实现用户认证
- [ ] 开发API接口
- [ ] 数据库设计

### 3. 测试和部署
- [ ] 编写单元测试
- [ ] 配置CI/CD
- [ ] 部署到生产环境

## 实现说明
详细的实现要求和注意事项...

## 期望的项目结构
\`\`\`
project/
├── src/
│   └── main.py
├── tests/
│   └── test_main.py
└── README.md
\`\`\`

## 注意事项
- 遵循代码规范
- 添加适当的注释
- 编写测试用例
```

## 🔧 常见问题

### Q1: 数据库迁移失败怎么办？

**A:** 检查是否有旧数据库文件，如果没有，直接跳过迁移步骤。

### Q2: 前端无法连接后端？

**A:** 确保后端服务已启动，检查端口是否被占用：
```bash
lsof -i :8000
```

### Q3: Markdown 渲染不正常？

**A:** 确保已安装 `marked` 库：
```bash
cd frontend
npm install marked
```

### Q4: 如何查看任务日志？

**A:**
- Web 界面：展开任务行或点击"查看"按钮
- API：获取任务详情时会包含 logs 字段

### Q5: 可以编辑已创建的任务吗？

**A:** 目前支持通过 API 更新任务：
```python
import requests
requests.put(f'http://localhost:8000/api/tasks/{task_id}', json={
    "markdown_document": "更新后的内容...",
    "overall_progress": 0.5
})
```

## 📚 更多资源

- [完整更新总结](COMPLETE_UPDATE_SUMMARY.md)
- [简化结构说明](SIMPLIFIED_TASK_STRUCTURE.md)
- [详细变更说明](TASK_STRUCTURE_CHANGES.md)
- [前端更新说明](frontend/FRONTEND_UPDATES.md)
- [示例任务](tasks/example_task.md)

## 🎉 开始使用

现在你已经准备好使用新的简化任务系统了！

如有任何问题，请查看文档或联系开发团队。

---

**提示**: 建议先创建一个测试任务熟悉系统，然后再创建实际的项目任务。
