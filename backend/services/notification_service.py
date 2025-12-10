"""
任务通知服务 - 负责在任务完成或失败时通知回调URL
"""
import httpx
import asyncio
from typing import Optional
from datetime import datetime
from backend.models.schemas import TaskNotificationPayload


class NotificationService:
    """任务通知服务"""

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """
        初始化通知服务

        Args:
            timeout: HTTP请求超时时间（秒）
            max_retries: 最大重试次数
        """
        self.timeout = timeout
        self.max_retries = max_retries

    async def send_notification(
        self,
        callback_url: str,
        task_id: str,
        status: str,
        project_directory: str,
        markdown_document_path: str,
        error_message: Optional[str] = None
    ) -> bool:
        """
        发送任务完成通知

        Args:
            callback_url: 回调URL
            task_id: 任务ID
            status: 任务状态 ("completed" 或 "failed")
            project_directory: 项目目录
            markdown_document_path: 文档路径
            error_message: 错误信息（如果失败）

        Returns:
            bool: 是否发送成功
        """
        if not callback_url:
            print(f"任务 {task_id} 没有配置回调URL，跳过通知")
            return False

        # 构建通知负载
        payload = TaskNotificationPayload(
            task_id=task_id,
            status=status,
            project_directory=project_directory,
            markdown_document_path=markdown_document_path,
            completed_at=datetime.now().isoformat(),
            error_message=error_message
        )

        # 尝试发送通知，带重试机制
        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        callback_url,
                        json=payload.model_dump(),
                        headers={"Content-Type": "application/json"}
                    )

                    if response.status_code in [200, 201, 202, 204]:
                        print(f"✅ 任务 {task_id} 通知发送成功 (状态: {status})")
                        return True
                    else:
                        print(f"⚠️  任务 {task_id} 通知失败 (HTTP {response.status_code}): {response.text}")

            except httpx.TimeoutException:
                print(f"⚠️  任务 {task_id} 通知超时 (尝试 {attempt}/{self.max_retries})")
            except httpx.RequestError as e:
                print(f"⚠️  任务 {task_id} 通知请求错误 (尝试 {attempt}/{self.max_retries}): {e}")
            except Exception as e:
                print(f"❌ 任务 {task_id} 通知发送异常: {e}")
                break

            # 如果不是最后一次尝试，等待后重试
            if attempt < self.max_retries:
                await asyncio.sleep(2 ** attempt)  # 指数退避

        print(f"❌ 任务 {task_id} 通知最终失败，已重试 {self.max_retries} 次")
        return False

    async def notify_task_completed(
        self,
        callback_url: str,
        task_id: str,
        project_directory: str,
        markdown_document_path: str
    ) -> bool:
        """
        通知任务完成

        Args:
            callback_url: 回调URL
            task_id: 任务ID
            project_directory: 项目目录
            markdown_document_path: 文档路径

        Returns:
            bool: 是否发送成功
        """
        return await self.send_notification(
            callback_url=callback_url,
            task_id=task_id,
            status="completed",
            project_directory=project_directory,
            markdown_document_path=markdown_document_path
        )

    async def notify_task_failed(
        self,
        callback_url: str,
        task_id: str,
        project_directory: str,
        markdown_document_path: str,
        error_message: str
    ) -> bool:
        """
        通知任务失败

        Args:
            callback_url: 回调URL
            task_id: 任务ID
            project_directory: 项目目录
            markdown_document_path: 文档路径
            error_message: 错误信息

        Returns:
            bool: 是否发送成功
        """
        return await self.send_notification(
            callback_url=callback_url,
            task_id=task_id,
            status="failed",
            project_directory=project_directory,
            markdown_document_path=markdown_document_path,
            error_message=error_message
        )
