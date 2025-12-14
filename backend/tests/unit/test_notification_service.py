"""
Notification Service Tests
测试通知服务
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from backend.services.notification_service import NotificationService


class TestNotificationService:
    """测试通知服务"""

    def test_init_default_values(self):
        """测试默认初始化值"""
        service = NotificationService()
        assert service.timeout == 30
        assert service.max_retries == 3

    def test_init_custom_values(self):
        """测试自定义初始化值"""
        service = NotificationService(timeout=60, max_retries=5)
        assert service.timeout == 60
        assert service.max_retries == 5


class TestSendNotification:
    """测试发送通知"""

    @pytest.mark.asyncio
    async def test_send_notification_success(self):
        """测试发送通知成功"""
        service = NotificationService()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await service.send_notification(
                callback_url="http://localhost:8080/callback",
                task_id="task_123",
                status="completed",
                project_directory="/tmp/project",
                markdown_document_path="/tmp/project/doc.md"
            )

            assert result is True
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_notification_no_callback_url(self):
        """测试没有回调 URL 时跳过"""
        service = NotificationService()

        result = await service.send_notification(
            callback_url="",
            task_id="task_123",
            status="completed",
            project_directory="/tmp/project",
            markdown_document_path="/tmp/project/doc.md"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_notification_none_callback_url(self):
        """测试回调 URL 为 None 时跳过"""
        service = NotificationService()

        result = await service.send_notification(
            callback_url=None,
            task_id="task_123",
            status="completed",
            project_directory="/tmp/project",
            markdown_document_path="/tmp/project/doc.md"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_notification_http_error(self):
        """测试 HTTP 错误响应"""
        service = NotificationService(max_retries=1)

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await service.send_notification(
                callback_url="http://localhost:8080/callback",
                task_id="task_123",
                status="completed",
                project_directory="/tmp/project",
                markdown_document_path="/tmp/project/doc.md"
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_send_notification_timeout(self):
        """测试请求超时"""
        service = NotificationService(max_retries=1)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await service.send_notification(
                callback_url="http://localhost:8080/callback",
                task_id="task_123",
                status="completed",
                project_directory="/tmp/project",
                markdown_document_path="/tmp/project/doc.md"
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_send_notification_request_error(self):
        """测试请求错误"""
        service = NotificationService(max_retries=1)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=httpx.RequestError("Connection refused"))
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await service.send_notification(
                callback_url="http://localhost:8080/callback",
                task_id="task_123",
                status="completed",
                project_directory="/tmp/project",
                markdown_document_path="/tmp/project/doc.md"
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_send_notification_general_exception(self):
        """测试通用异常"""
        service = NotificationService(max_retries=2)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=Exception("Unexpected error"))
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await service.send_notification(
                callback_url="http://localhost:8080/callback",
                task_id="task_123",
                status="completed",
                project_directory="/tmp/project",
                markdown_document_path="/tmp/project/doc.md"
            )

            assert result is False
            # 通用异常不会重试，只会调用一次
            assert mock_client.post.call_count == 1

    @pytest.mark.asyncio
    async def test_send_notification_accepts_multiple_success_codes(self):
        """测试接受多种成功状态码"""
        service = NotificationService()

        for status_code in [200, 201, 202, 204]:
            mock_response = MagicMock()
            mock_response.status_code = status_code
            mock_response.text = "OK"

            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(return_value=mock_response)
                mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

                result = await service.send_notification(
                    callback_url="http://localhost:8080/callback",
                    task_id="task_123",
                    status="completed",
                    project_directory="/tmp/project",
                    markdown_document_path="/tmp/project/doc.md"
                )

                assert result is True, f"Status code {status_code} should be accepted"

    @pytest.mark.asyncio
    async def test_send_notification_with_error_message(self):
        """测试带错误信息的通知"""
        service = NotificationService()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await service.send_notification(
                callback_url="http://localhost:8080/callback",
                task_id="task_123",
                status="failed",
                project_directory="/tmp/project",
                markdown_document_path="/tmp/project/doc.md",
                error_message="Something went wrong"
            )

            assert result is True
            # 验证 post 被调用时包含 error_message
            call_args = mock_client.post.call_args
            assert "error_message" in call_args.kwargs["json"]
            assert call_args.kwargs["json"]["error_message"] == "Something went wrong"


class TestNotifyTaskCompleted:
    """测试任务完成通知"""

    @pytest.mark.asyncio
    async def test_notify_task_completed(self):
        """测试任务完成通知"""
        service = NotificationService()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await service.notify_task_completed(
                callback_url="http://localhost:8080/callback",
                task_id="task_123",
                project_directory="/tmp/project",
                markdown_document_path="/tmp/project/doc.md"
            )

            assert result is True
            # 验证状态是 completed
            call_args = mock_client.post.call_args
            assert call_args.kwargs["json"]["status"] == "completed"


class TestNotifyTaskFailed:
    """测试任务失败通知"""

    @pytest.mark.asyncio
    async def test_notify_task_failed(self):
        """测试任务失败通知"""
        service = NotificationService()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await service.notify_task_failed(
                callback_url="http://localhost:8080/callback",
                task_id="task_123",
                project_directory="/tmp/project",
                markdown_document_path="/tmp/project/doc.md",
                error_message="Task execution failed"
            )

            assert result is True
            # 验证状态是 failed 且有 error_message
            call_args = mock_client.post.call_args
            assert call_args.kwargs["json"]["status"] == "failed"
            assert call_args.kwargs["json"]["error_message"] == "Task execution failed"
