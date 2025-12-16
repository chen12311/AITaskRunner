"""
Template Service - 管理提示模板 - 异步版本
"""
from pathlib import Path
from typing import List, Optional

from backend.database.models import Database, TemplateDAO
from backend.models.schemas import (
    TemplateModel, TemplateCreateRequest, TemplateUpdateRequest
)


class TemplateService:
    """模板服务 - 异步版本"""

    def __init__(self, db_path: str = "aitaskrunner.db", db: Database = None):
        """
        初始化模板服务

        优化6.2: 支持注入共享数据库实例

        Args:
            db_path: 数据库文件路径（如果 db 为 None 时使用）
            db: 共享的数据库实例（优先使用）
        """
        if db is not None:
            self.db = db
        else:
            self.db = Database(db_path)
        self.template_dao = TemplateDAO(self.db)
        self._initialized = False

    async def initialize(self):
        """初始化数据库和默认模板"""
        if not self._initialized:
            await self.db.initialize()
            # 初始化默认模板
            await self._init_default_templates()
            self._initialized = True

    async def _init_default_templates(self):
        """初始化默认模板（如果不存在）"""
        existing = await self.template_dao.get_all_templates()

        # 检查是否需要添加 continue_task 模板（升级兼容）
        if existing:
            existing_types = {t['type'] for t in existing}
            if 'continue_task' not in existing_types:
                await self._add_continue_task_template()
            return

        # 创建默认模板
        default_templates = [
            {
                'id': 'tpl_initial_default',
                'name': '项目经理模式 - 初始任务',
                'type': 'initial_task',
                'content': '''你是项目经理。请根据以下需求文档制定开发计划并监督执行：

@{doc_path}

项目目录: {project_dir}
任务ID: {task_id}
API回调地址: {api_base_url}

**你的职责**:
1. 分析文档，理解所有需求和任务清单
2. 将每个任务分解为具体的开发步骤
3. 调用 Claude Code 执行具体的编码工作
4. 审查 Claude Code 的执行结果
5. 确认质量后更新文档中的 checkbox ([ ] 改为 [x])

**工作流程**:
对于文档中的每个未完成任务项 ([ ]):

1. **规划**: 分析任务需求，制定实现方案
2. **执行**: 指导 Claude Code 完成具体编码
3. **审查**: 检查代码质量、功能正确性、测试覆盖
4. **确认**: 审查通过后更新 checkbox 为 [x]

**质量要求**:
- 代码符合最佳实践
- 有适当的错误处理
- 必要时编写测试
- 代码有清晰的注释

**⚠️ 重要：状态回调（必须执行）**:
任务执行过程中和完成后，**必须**调用状态通知接口，否则系统无法追踪任务状态：

```bash
# 当前会话完成（还有剩余任务时）
curl -X POST {api_base_url}/api/tasks/{task_id}/notify-status \
  -H "Content-Type: application/json" \
  -d '{{"status": "session_completed", "message": "当前会话完成"}}'

# 所有任务完成
curl -X POST {api_base_url}/api/tasks/{task_id}/notify-status \
  -H "Content-Type: application/json" \
  -d '{{"status": "completed", "message": "所有任务已完成"}}'

# 任务失败/遇到无法解决的问题
curl -X POST {api_base_url}/api/tasks/{task_id}/notify-status \
  -H "Content-Type: application/json" \
  -d '{{"status": "failed", "error": "错误描述"}}'
```

**重要提醒**:
- 你负责思考和决策，Claude Code 负责执行
- 每完成一个任务项，立即更新文档状态
- 遇到问题时，重新规划并指导修正
- 保持项目目录结构清晰
- **完成或退出前必须调用状态回调接口**

现在开始：
1. 首先阅读并分析整个需求文档
2. 然后从第一个未完成的任务项开始规划和执行
''',
                'description': 'Codex 作为项目经理，规划任务并指导 Claude Code 执行',
                'is_default': 1
            },
            {
                'id': 'tpl_resume_default',
                'name': '项目经理模式 - 恢复任务',
                'type': 'resume_task',
                'content': '''会话已重启，请继续担任项目经理角色：

@{doc_path}

项目目录: {project_dir}
任务ID: {task_id}
API回调地址: {api_base_url}

**恢复工作**:
1. 重新阅读文档，了解整体进度
2. 识别已完成的任务 ([x]) 和未完成的任务 ([ ])
3. 从第一个未完成的任务继续
4. 保持之前的工作流程：规划 → 执行 → 审查 → 确认

**检查清单**:
- [ ] 确认项目目录结构
- [ ] 检查已完成的代码
- [ ] 识别下一个待完成任务
- [ ] 制定继续执行的计划

**🔴 上下文自动管理（极其重要 - 必须遵守）**:
你必须**主动监控上下文使用情况**，当出现以下任何情况时，**立即停止当前工作并调用 session_completed**：

 *触发条件（满足任一即触发）**:
1. 对话轮次达到 **10-15 轮**（每次你回复算一轮）
2. 已完成 **2-3 个任务项**（checkbox 从 [ ] 变为 [x]）
3. 执行了大量文件读写操作（超过 10 个文件）
4. 你感觉响应开始变慢或需要重新阅读之前的内容
5. 单个任务特别复杂，涉及多文件修改

**⚠️ 不要等到"卡住"或"忘记上下文"才调用** - 这时已经太晚了！
**✅ 在合适的时机主动保存进度**，系统会自动重启新会话继续执行。


**⚠️ 重要：状态回调（必须执行）**:
任务执行过程中和完成后，**必须**调用状态通知接口：

```bash
# 当前会话完成（还有剩余任务时）
curl -X POST {api_base_url}/api/tasks/{task_id}/notify-status \
  -H "Content-Type: application/json" \
  -d '{{"status": "session_completed", "message": "继续执行"}}'

# 所有任务完成
curl -X POST {api_base_url}/api/tasks/{task_id}/notify-status \
  -H "Content-Type: application/json" \
  -d '{{"status": "completed", "message": "所有任务已完成"}}'

# 任务失败
curl -X POST {api_base_url}/api/tasks/{task_id}/notify-status \
  -H "Content-Type: application/json" \
  -d '{{"status": "failed", "error": "错误描述"}}'
```

**注意**：不调用回调会导致系统无法追踪任务状态！

现在开始恢复工作，继续监督和审查 Claude Code 的执行。完成或退出前**必须**调用状态回调。
''',
                'description': '会话重启后恢复工作',
                'is_default': 1
            },
            {
                'id': 'tpl_review_default',
                'name': '项目完成审查',
                'type': 'review',
                'content': '''所有任务已执行完毕，请进行最终审查：

@{doc_path}

项目目录: {project_dir}
任务ID: {task_id}
API回调地址: {api_base_url}

**审查范围**:
1. 检查文档中所有标记为完成 [x] 的任务
2. 验证每个任务的实现是否符合需求
3. 检查代码质量和潜在问题

**审查清单**:
- [ ] 代码是否正确实现了所有需求？
- [ ] 是否有语法错误或明显 bug？
- [ ] 代码风格是否一致？
- [ ] 是否有适当的错误处理？
- [ ] 是否需要补充测试？
- [ ] 文档/注释是否充分？

**审查后操作**:
- 如果发现问题需要修复，请直接修复
- 修复完成后更新文档中的相关说明

**📌 审查进度标记（重要）**:
为了在会话重启后能够继续审查，请在每个任务审查通过后添加标记：
- **跳过**已标记 `✅已审查` 的任务（表示之前已审查通过）
- 审查通过后，在该任务行**末尾**添加 `✅已审查` 标记

示例：
```
修改前: - [x] 实现用户登录功能
修改后: - [x] 实现用户登录功能 ✅已审查
```

**⚠️ 重要：状态回调（必须执行）**:
审查完成后，**必须**调用以下状态通知接口之一，否则系统无法追踪任务状态：

```bash
# 审查完成（还有问题需要处理）
curl -X POST {api_base_url}/api/tasks/{task_id}/notify-status \\
  -H "Content-Type: application/json" \\
  -d '{{"status": "review_session_completed", "message": "审查发现问题，需要继续处理"}}'

# 审查通过，所有任务完成
curl -X POST {api_base_url}/api/tasks/{task_id}/notify-status \\
  -H "Content-Type: application/json" \\
  -d '{{"status": "review_completed", "message": "审查通过，所有任务已完成"}}'
```

**注意**：不调用回调会导致任务状态无法更新！

现在开始审查工作。审查完成或退出前**必须**调用状态回调。
''',
                'description': '任务完成后的项目级审查',
                'is_default': 1
            },
            {
                'id': 'tpl_continue_default',
                'name': '异常恢复 - 继续任务',
                'type': 'continue_task',
                'content': '''检测到任务可能异常停止，请继续执行：

@{doc_path}

项目目录: {project_dir}
任务ID: {task_id}
API回调地址: {api_base_url}

**请检查**:
1. 查看文档中的任务进度（已完成 [x] 和未完成 [ ]）
2. 确认当前工作状态
3. 继续执行未完成的任务

**⚠️ 重要：状态回调（必须执行）**:
任务执行过程中和完成后，**必须**调用状态通知接口，否则系统无法追踪任务状态：

```bash
# 会话完成（还有剩余任务）
curl -X POST {api_base_url}/api/tasks/{task_id}/notify-status \\
  -H "Content-Type: application/json" \\
  -d '{{"status": "session_completed", "message": "继续执行"}}'

# 所有任务完成
curl -X POST {api_base_url}/api/tasks/{task_id}/notify-status \\
  -H "Content-Type: application/json" \\
  -d '{{"status": "completed", "message": "所有任务已完成"}}'

# 任务失败
curl -X POST {api_base_url}/api/tasks/{task_id}/notify-status \\
  -H "Content-Type: application/json" \\
  -d '{{"status": "failed", "error": "错误描述"}}'
```

**注意**：不调用回调会导致系统无法追踪任务状态！

现在请继续执行任务。完成或退出前**必须**调用状态回调。
''',
                'description': '异常停止后自动恢复的提示词',
                'is_default': 1
            }
        ]

        for tpl in default_templates:
            await self.template_dao.create_template(tpl)

    async def _add_continue_task_template(self):
        """添加 continue_task 模板（升级兼容）"""
        continue_template = {
            'id': 'tpl_continue_default',
            'name': '异常恢复 - 继续任务',
            'type': 'continue_task',
            'content': '''检测到任务可能异常停止，请继续执行：

@{doc_path}

项目目录: {project_dir}
任务ID: {task_id}
API回调地址: {api_base_url}

**请检查**:
1. 查看文档中的任务进度（已完成 [x] 和未完成 [ ]）
2. 确认当前工作状态
3. 继续执行未完成的任务

**⚠️ 重要：状态回调（必须执行）**:
任务执行过程中和完成后，**必须**调用状态通知接口，否则系统无法追踪任务状态：

```bash
# 会话完成（还有剩余任务）
curl -X POST {api_base_url}/api/tasks/{task_id}/notify-status \\
  -H "Content-Type: application/json" \\
  -d '{"status": "session_completed", "message": "继续执行"}'

# 所有任务完成
curl -X POST {api_base_url}/api/tasks/{task_id}/notify-status \\
  -H "Content-Type: application/json" \\
  -d '{"status": "completed", "message": "所有任务已完成"}'

# 任务失败
curl -X POST {api_base_url}/api/tasks/{task_id}/notify-status \\
  -H "Content-Type: application/json" \\
  -d '{"status": "failed", "error": "错误描述"}'
```

**注意**：不调用回调会导致系统无法追踪任务状态！

现在请继续执行任务。完成或退出前**必须**调用状态回调。
''',
            'description': '异常停止后自动恢复的提示词',
            'is_default': 1
        }
        await self.template_dao.create_template(continue_template)

    async def get_all_templates(self) -> List[TemplateModel]:
        """获取所有模板"""
        await self.initialize()
        templates = await self.template_dao.get_all_templates()
        return [self._convert_to_model(t) for t in templates]

    async def get_template(self, template_id: str) -> Optional[TemplateModel]:
        """获取单个模板"""
        await self.initialize()
        template = await self.template_dao.get_template(template_id)
        if template:
            return self._convert_to_model(template)
        return None

    async def get_templates_by_type(self, template_type: str) -> List[TemplateModel]:
        """获取指定类型的所有模板"""
        await self.initialize()
        templates = await self.template_dao.get_templates_by_type(template_type)
        return [self._convert_to_model(t) for t in templates]

    async def get_default_template(self, template_type: str) -> Optional[TemplateModel]:
        """获取指定类型的默认模板"""
        await self.initialize()
        template = await self.template_dao.get_template_by_type(template_type, use_default=True)
        if template:
            return self._convert_to_model(template)
        return None

    async def create_template(self, request: TemplateCreateRequest) -> TemplateModel:
        """创建新模板"""
        await self.initialize()
        template_data = {
            'name': request.name,
            'type': request.type,
            'content': request.content,
            'content_en': request.content_en,
            'description': request.description or '',
            'is_default': 1 if request.is_default else 0
        }

        # 如果设为默认，先清除其他默认
        if request.is_default:
            existing_defaults = await self.template_dao.get_templates_by_type(request.type)
            for tpl in existing_defaults:
                if tpl.get('is_default'):
                    await self.template_dao.update_template(tpl['id'], {'is_default': 0})

        template_id = await self.template_dao.create_template(template_data)
        return await self.get_template(template_id)

    async def update_template(self, template_id: str, request: TemplateUpdateRequest) -> Optional[TemplateModel]:
        """更新模板"""
        await self.initialize()
        updates = {}

        if request.name is not None:
            updates['name'] = request.name
        if request.type is not None:
            updates['type'] = request.type
        if request.content is not None:
            updates['content'] = request.content
        if request.content_en is not None:
            updates['content_en'] = request.content_en
        if request.description is not None:
            updates['description'] = request.description
        if request.is_default is not None:
            if request.is_default:
                # 设为默认前先清除其他默认
                template = await self.template_dao.get_template(template_id)
                if template:
                    tpl_type = request.type or template['type']
                    existing_defaults = await self.template_dao.get_templates_by_type(tpl_type)
                    for tpl in existing_defaults:
                        if tpl.get('is_default') and tpl['id'] != template_id:
                            await self.template_dao.update_template(tpl['id'], {'is_default': 0})
            updates['is_default'] = 1 if request.is_default else 0

        if updates:
            success = await self.template_dao.update_template(template_id, updates)
            if success:
                return await self.get_template(template_id)

        return None

    async def delete_template(self, template_id: str) -> bool:
        """删除模板"""
        await self.initialize()
        return await self.template_dao.delete_template(template_id)

    async def set_default_template(self, template_id: str) -> bool:
        """设置默认模板"""
        await self.initialize()
        return await self.template_dao.set_default_template(template_id)

    async def render_template(self, template_type: str, locale: str = 'zh', **kwargs) -> str:
        """
        渲染模板，替换变量（为兼容性保留的便捷方法）

        Args:
            template_type: 模板类型
            locale: 语言代码 ('zh' 或 'en')
            **kwargs: 模板变量

        Returns:
            渲染后的模板内容
        """
        return await self.render_template_async(template_type, locale=locale, **kwargs)

    async def render_template_async(self, template_type: str, locale: str = 'zh', **kwargs) -> str:
        """
        渲染模板，替换变量（异步版本）

        Args:
            template_type: 模板类型
            locale: 语言代码 ('zh' 或 'en')
            **kwargs: 模板变量

        Returns:
            渲染后的模板内容
        """
        await self.initialize()
        template = await self.get_default_template(template_type)
        if not template:
            raise ValueError(f"No default template found for type: {template_type}")

        # 根据语言选择内容
        if locale == 'en' and template.content_en:
            content = template.content_en
        else:
            # 默认使用中文，或者当英文不存在时 fallback 到中文
            content = template.content

        # 替换变量
        for key, value in kwargs.items():
            content = content.replace(f"{{{key}}}", str(value))

        return content

    def _convert_to_model(self, template_dict: dict) -> TemplateModel:
        """转换为 Pydantic 模型"""
        return TemplateModel(
            id=template_dict['id'],
            name=template_dict['name'],
            name_en=template_dict.get('name_en'),
            type=template_dict['type'],
            content=template_dict['content'],
            content_en=template_dict.get('content_en'),
            description=template_dict.get('description', ''),
            description_en=template_dict.get('description_en'),
            is_default=bool(template_dict.get('is_default', 0)),
            created_at=template_dict.get('created_at', ''),
            updated_at=template_dict.get('updated_at', '')
        )
