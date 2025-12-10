"""
任务管理器 - Codex 规划和审查，Claude Code 执行
"""
from pathlib import Path
from typing import Optional


class TaskTemplate:
    """任务模板 - 生成发送给 Codex 的消息"""

    @staticmethod
    def get_initial_task_message(project_dir: str, doc_path: str, task_id: str = None, api_base_url: str = "http://127.0.0.1:8086") -> str:
        """获取初始任务消息 - Codex 作为项目经理"""

        # 构建任务信息部分
        task_info = ""
        if task_id:
            task_info = f"""
**任务信息**:
- 任务ID: {task_id}
- API地址: {api_base_url}
- 状态通知接口: {api_base_url}/api/tasks/{task_id}/notify-status
"""

        return f"""你是项目经理。请根据以下需求文档制定开发计划并监督执行：

@{doc_path}

项目目录: {project_dir}
{task_info}

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

**重要提醒**:
- 你负责思考和决策，Claude Code 负责执行
- 每完成一个任务项，立即更新文档状态
- 遇到问题时，重新规划并指导修正
- 保持项目目录结构清晰

**⚠️ 任务完成后必须调用状态通知接口**:

这是**强制步骤**，任务完成时必须执行以下操作：

**状态通知规则（仅两种情况）**:

```bash
# 情况1: 当前会话完成了部分任务，文档中还有未完成的 [ ] 项
# 使用场景：上下文快满了、完成了当前批次任务、需要分批执行等
curl -X POST {api_base_url}/api/tasks/{task_id}/notify-status \\
  -H "Content-Type: application/json" \\
  -d '{{"status": "session_completed", "message": "当前会话任务完成，还有剩余任务"}}'
# 系统会自动检查进度，如果还有未完成任务会自动重启新会话继续执行

# 情况2: 文档中所有任务都已完成（所有 [ ] 都变成了 [x]）
# ⚠️ 必须确认文档完成率 100% 才能使用此状态
curl -X POST {api_base_url}/api/tasks/{task_id}/notify-status \\
  -H "Content-Type: application/json" \\
  -d '{{"status": "completed", "message": "所有任务已完成"}}'
```

**关键规则**:
1. **只能使用以上两种状态**: `session_completed` 或 `completed`
2. **completed 的使用条件**: 必须在确认文档中**所有 [ ] 都已变成 [x]** 后才能使用
3. **默认使用 session_completed**: 如果不确定是否全部完成，使用 `session_completed`，系统会自动检查并决定是否继续
4. **系统会自动验证**: 即使误用 `completed`，后端也会验证文档完成率并自动纠正

**执行检查清单**:
- [ ] 已执行上述 curl 命令通知系统状态
- [ ] 确认命令执行成功（返回 success: true）
- [ ] 使用 interactive_feedback 向用户汇报完成情况

现在开始：
1. 首先阅读并分析整个需求文档
2. 然后从第一个未完成的任务项开始规划和执行
3. 根据实际情况使用合适的通知状态
"""

    @staticmethod
    def get_resume_task_message(project_dir: str, doc_path: str, task_id: str = None, api_base_url: str = "http://127.0.0.1:8086") -> str:
        """获取恢复任务消息 - 会话重启后继续"""

        # 构建任务信息部分
        task_info = ""
        if task_id:
            task_info = f"""
**任务信息**:
- 任务ID: {task_id}
- API地址: {api_base_url}
- 状态通知接口: {api_base_url}/api/tasks/{task_id}/notify-status
"""

        return f"""会话已重启，请继续担任项目经理角色：

@{doc_path}

项目目录: {project_dir}
{task_info}

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

**⚠️ 任务完成后必须调用状态通知接口**:

这是**强制步骤**，任务完成时必须执行以下操作：

**状态通知规则（仅两种情况）**:

```bash
# 情况1: 当前会话完成了部分任务，文档中还有未完成的 [ ] 项
# 使用场景：上下文快满了、完成了当前批次任务、需要分批执行等
curl -X POST {api_base_url}/api/tasks/{task_id}/notify-status \\
  -H "Content-Type: application/json" \\
  -d '{{"status": "session_completed", "message": "当前会话任务完成，还有剩余任务"}}'
# 系统会自动检查进度，如果还有未完成任务会自动重启新会话继续执行

# 情况2: 文档中所有任务都已完成（所有 [ ] 都变成了 [x]）
# ⚠️ 必须确认文档完成率 100% 才能使用此状态
curl -X POST {api_base_url}/api/tasks/{task_id}/notify-status \\
  -H "Content-Type: application/json" \\
  -d '{{"status": "completed", "message": "所有任务已完成"}}'
```

**关键规则**:
1. **只能使用以上两种状态**: `session_completed` 或 `completed`
2. **completed 的使用条件**: 必须在确认文档中**所有 [ ] 都已变成 [x]** 后才能使用
3. **默认使用 session_completed**: 如果不确定是否全部完成，使用 `session_completed`，系统会自动检查并决定是否继续
4. **系统会自动验证**: 即使误用 `completed`，后端也会验证文档完成率并自动纠正
5. **本次会话是续接**: 说明之前会话已完成部分任务，继续完成剩余的未完成任务 ([ ])

**执行检查清单**:
- [ ] 已执行上述 curl 命令通知系统状态
- [ ] 确认命令执行成功（返回 success: true）
- [ ] 使用 interactive_feedback 向用户汇报完成情况

现在开始恢复工作，继续监督和审查 Claude Code 的执行。
"""
