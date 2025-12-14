"""
Markdown Checker Tests
测试 Markdown 文档进度检查工具
"""
import pytest
import tempfile
import os
from pathlib import Path

from backend.utils.markdown_checker import (
    check_remaining_tasks,
    clear_cache,
    get_task_progress_summary,
    _is_optional_section_header,
    _is_optional_task,
    _get_header_level,
    _parse_tasks_with_optional_filter
)


class TestHelperFunctions:
    """测试辅助函数"""

    def test_is_optional_section_header_chinese(self):
        """测试中文可选标题识别"""
        assert _is_optional_section_header("## 可选功能") is True
        assert _is_optional_section_header("### 可选项") is True
        assert _is_optional_section_header("# 可选") is True

    def test_is_optional_section_header_english(self):
        """测试英文可选标题识别"""
        assert _is_optional_section_header("## Optional Features") is True
        assert _is_optional_section_header("### OPTIONAL") is True
        assert _is_optional_section_header("# optional items") is True

    def test_is_optional_section_header_not_optional(self):
        """测试非可选标题"""
        assert _is_optional_section_header("## Required Features") is False
        assert _is_optional_section_header("### Core Tasks") is False
        assert _is_optional_section_header("Normal text") is False

    def test_is_optional_section_header_not_header(self):
        """测试非标题行"""
        assert _is_optional_section_header("可选功能") is False
        assert _is_optional_section_header("Optional Features") is False
        assert _is_optional_section_header("- [ ] 可选") is False

    def test_is_optional_task_chinese(self):
        """测试中文可选任务识别"""
        assert _is_optional_task("- [ ] 实现可选功能") is True
        assert _is_optional_task("- [x] 可选：添加日志") is True

    def test_is_optional_task_english(self):
        """测试英文可选任务识别"""
        assert _is_optional_task("- [ ] Optional: Add logging") is True
        assert _is_optional_task("- [x] (optional) feature") is True

    def test_is_optional_task_required(self):
        """测试必选任务"""
        assert _is_optional_task("- [ ] Required feature") is False
        assert _is_optional_task("- [x] Core functionality") is False

    def test_get_header_level(self):
        """测试获取标题级别"""
        assert _get_header_level("# Title") == 1
        assert _get_header_level("## Subtitle") == 2
        assert _get_header_level("### Section") == 3
        assert _get_header_level("###### Deep") == 6
        assert _get_header_level("Normal text") == 0
        assert _get_header_level("- [ ] Task") == 0


class TestParseTasksWithOptionalFilter:
    """测试任务解析和过滤"""

    def test_parse_simple_tasks(self):
        """测试解析简单任务列表"""
        content = """
# Tasks

- [ ] Task 1
- [x] Task 2
- [ ] Task 3
"""
        unchecked, checked, optional = _parse_tasks_with_optional_filter(content)
        assert len(unchecked) == 2
        assert len(checked) == 1
        assert len(optional) == 0

    def test_parse_tasks_with_optional_section(self):
        """测试解析包含可选章节的任务"""
        content = """
# Required Tasks

- [ ] Required 1
- [x] Required 2

## 可选功能

- [ ] Optional 1
- [x] Optional 2
"""
        unchecked, checked, optional = _parse_tasks_with_optional_filter(content)
        assert len(unchecked) == 1
        assert len(checked) == 1
        assert len(optional) == 2

    def test_parse_tasks_with_inline_optional(self):
        """测试解析内联可选任务"""
        content = """
# Tasks

- [ ] Required task
- [ ] Optional: This is optional
- [x] 可选：这也是可选的
"""
        unchecked, checked, optional = _parse_tasks_with_optional_filter(content)
        assert len(unchecked) == 1
        assert len(checked) == 0
        assert len(optional) == 2

    def test_parse_nested_sections(self):
        """测试嵌套章节"""
        content = """
# Main

- [ ] Main task 1

## 可选章节

- [ ] Optional task

### Subsection in optional

- [ ] Still optional

## Required Section

- [ ] Back to required
"""
        unchecked, checked, optional = _parse_tasks_with_optional_filter(content)
        assert len(unchecked) == 2  # Main task 1, Back to required
        assert len(checked) == 0
        assert len(optional) == 2  # Optional task, Still optional

    def test_parse_empty_content(self):
        """测试空内容"""
        unchecked, checked, optional = _parse_tasks_with_optional_filter("")
        assert len(unchecked) == 0
        assert len(checked) == 0
        assert len(optional) == 0

    def test_parse_different_list_markers(self):
        """测试不同的列表标记"""
        content = """
- [ ] Dash unchecked
- [x] Dash checked
* [ ] Asterisk unchecked
* [X] Asterisk checked
+ [ ] Plus unchecked
+ [x] Plus checked
"""
        unchecked, checked, optional = _parse_tasks_with_optional_filter(content)
        assert len(unchecked) == 3
        assert len(checked) == 3


class TestCheckRemainingTasks:
    """测试检查剩余任务"""

    def test_check_remaining_tasks_with_file(self):
        """测试从文件检查剩余任务"""
        content = """
# Test Plan

- [x] Completed task 1
- [ ] Pending task 1
- [ ] Pending task 2
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            clear_cache()  # 清除缓存
            result = check_remaining_tasks(temp_path)

            assert result["has_remaining"] is True
            assert result["total"] == 3
            assert result["completed"] == 1
            assert result["remaining"] == 2
            assert result["optional"] == 0
            assert "error" not in result
        finally:
            os.unlink(temp_path)

    def test_check_remaining_tasks_all_completed(self):
        """测试所有任务已完成"""
        content = """
- [x] Task 1
- [x] Task 2
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            clear_cache()
            result = check_remaining_tasks(temp_path)

            assert result["has_remaining"] is False
            assert result["total"] == 2
            assert result["completed"] == 2
            assert result["remaining"] == 0
        finally:
            os.unlink(temp_path)

    def test_check_remaining_tasks_nonexistent_file(self):
        """测试不存在的文件"""
        result = check_remaining_tasks("/nonexistent/path/file.md")

        assert result["has_remaining"] is False
        assert result["total"] == 0
        assert "error" in result
        assert "文档不存在" in result["error"]

    def test_check_remaining_tasks_with_optional_excluded(self):
        """测试排除可选任务"""
        content = """
# Tasks

- [x] Required done
- [ ] Required pending

## 可选功能

- [ ] Optional 1
- [ ] Optional 2
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            clear_cache()
            result = check_remaining_tasks(temp_path)

            assert result["total"] == 2  # Only required tasks
            assert result["completed"] == 1
            assert result["remaining"] == 1
            assert result["optional"] == 2
        finally:
            os.unlink(temp_path)

    def test_check_remaining_tasks_cache(self):
        """测试缓存功能"""
        content = "- [ ] Task 1"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            clear_cache()

            # First call - should read file
            result1 = check_remaining_tasks(temp_path, use_cache=True)
            assert result1["remaining"] == 1

            # Modify file content (without changing mtime significantly)
            with open(temp_path, 'w') as f:
                f.write("- [x] Task 1")

            # Second call with cache - should return cached result
            result2 = check_remaining_tasks(temp_path, use_cache=True)
            # Note: Cache might still return old result if within TTL
            # This is expected behavior

            # Call without cache - should read new content
            clear_cache()
            result3 = check_remaining_tasks(temp_path, use_cache=False)
            assert result3["remaining"] == 0
        finally:
            os.unlink(temp_path)


class TestClearCache:
    """测试清除缓存"""

    def test_clear_specific_cache(self):
        """测试清除特定文档缓存"""
        content = "- [ ] Task"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            # Populate cache
            check_remaining_tasks(temp_path)

            # Clear specific cache
            clear_cache(temp_path)

            # Modify file
            with open(temp_path, 'w') as f:
                f.write("- [x] Task")

            # Should read new content
            result = check_remaining_tasks(temp_path)
            assert result["remaining"] == 0
        finally:
            os.unlink(temp_path)

    def test_clear_all_cache(self):
        """测试清除所有缓存"""
        clear_cache()  # Clear all
        # No assertion needed - just verify it doesn't raise


class TestGetTaskProgressSummary:
    """测试获取任务进度摘要"""

    def test_progress_summary_normal(self):
        """测试正常进度摘要"""
        content = """
- [x] Done 1
- [x] Done 2
- [ ] Pending 1
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            clear_cache()
            summary = get_task_progress_summary(temp_path)
            assert "2/3 completed" in summary
            assert "1 remaining" in summary
        finally:
            os.unlink(temp_path)

    def test_progress_summary_with_optional(self):
        """测试包含可选任务的进度摘要"""
        content = """
- [x] Done
- [ ] Pending

## Optional

- [ ] Optional task
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            clear_cache()
            summary = get_task_progress_summary(temp_path)
            assert "1/2 completed" in summary
            assert "1 remaining" in summary
            assert "1 optional excluded" in summary
        finally:
            os.unlink(temp_path)

    def test_progress_summary_no_tasks(self):
        """测试无任务的进度摘要"""
        content = "# Empty document\n\nNo tasks here."
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            clear_cache()
            summary = get_task_progress_summary(temp_path)
            assert "No tasks found" in summary
        finally:
            os.unlink(temp_path)

    def test_progress_summary_error(self):
        """测试错误时的进度摘要"""
        summary = get_task_progress_summary("/nonexistent/file.md")
        assert "Error:" in summary

    def test_progress_summary_all_completed(self):
        """测试全部完成的进度摘要"""
        content = """
- [x] Done 1
- [x] Done 2
- [x] Done 3
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            clear_cache()
            summary = get_task_progress_summary(temp_path)
            assert "3/3 completed" in summary
            assert "0 remaining" in summary
        finally:
            os.unlink(temp_path)


class TestEdgeCases:
    """测试边界情况"""

    def test_indented_tasks(self):
        """测试缩进的任务"""
        content = """
- [ ] Top level
  - [ ] Indented level 1
    - [ ] Indented level 2
"""
        unchecked, checked, optional = _parse_tasks_with_optional_filter(content)
        assert len(unchecked) == 3

    def test_mixed_checkbox_styles(self):
        """测试混合复选框样式"""
        content = """
- [x] Lowercase x
- [X] Uppercase X
- [ ] Empty checkbox
- [  ] Double space (invalid)
"""
        unchecked, checked, optional = _parse_tasks_with_optional_filter(content)
        # [x] and [X] should both be recognized as checked
        assert len(checked) == 2
        assert len(unchecked) == 1  # Only single space empty checkbox

    def test_unicode_content(self):
        """测试 Unicode 内容"""
        content = """
# 测试计划

- [x] 完成中文任务
- [ ] 待处理任务 🚀
- [ ] 可选：日语テスト
"""
        unchecked, checked, optional = _parse_tasks_with_optional_filter(content)
        assert len(checked) == 1
        assert len(unchecked) == 1
        assert len(optional) == 1

    def test_task_with_special_characters(self):
        """测试包含特殊字符的任务"""
        content = """
- [ ] Task with `code`
- [x] Task with **bold**
- [ ] Task with [link](url)
- [x] Task with <html>tags</html>
"""
        unchecked, checked, optional = _parse_tasks_with_optional_filter(content)
        assert len(unchecked) == 2
        assert len(checked) == 2
