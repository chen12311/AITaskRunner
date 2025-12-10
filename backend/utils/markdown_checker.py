"""
Markdown文档进度检查工具 - 检测任务完成情况
"""
import re
import time
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple

# 优化4.1: 使用简单的 TTL 缓存来缓存 Markdown 解析结果
_cache: Dict[str, Dict] = {}
_cache_timestamps: Dict[str, float] = {}
CACHE_TTL = 30  # 30秒缓存过期


def _is_optional_section_header(line: str) -> bool:
    """检查是否为可选章节的标题"""
    # 匹配 markdown 标题（# ## ### 等）
    if not re.match(r'^#{1,6}\s+', line):
        return False
    # 检查标题是否包含"可选"或"optional"（不区分大小写）
    lower_line = line.lower()
    return '可选' in line or 'optional' in lower_line


def _is_optional_task(task_line: str) -> bool:
    """检查单个任务是否标记为可选"""
    lower_line = task_line.lower()
    return '可选' in task_line or 'optional' in lower_line


def _get_header_level(line: str) -> int:
    """获取标题级别，非标题返回 0"""
    match = re.match(r'^(#{1,6})\s+', line)
    return len(match.group(1)) if match else 0


def _parse_tasks_with_optional_filter(content: str) -> Tuple[List[str], List[str], List[str]]:
    """
    解析文档中的任务，区分必选和可选任务

    Returns:
        Tuple: (必选未完成任务列表, 必选已完成任务列表, 可选任务列表)
    """
    lines = content.split('\n')

    required_unchecked = []
    required_checked = []
    optional_tasks = []

    # 跟踪当前是否在可选章节内
    in_optional_section = False
    optional_section_level = 0

    # 任务匹配模式
    unchecked_pattern = r'^[\s]*[-\*\+]\s*\[\s\]\s*(.+)$'
    checked_pattern = r'^[\s]*[-\*\+]\s*\[[xX]\]\s*(.+)$'

    for line in lines:
        # 检查是否为标题行
        header_level = _get_header_level(line)

        if header_level > 0:
            # 如果遇到新标题
            if _is_optional_section_header(line):
                # 进入可选章节
                in_optional_section = True
                optional_section_level = header_level
            elif in_optional_section and header_level <= optional_section_level:
                # 遇到同级或更高级别的标题，退出可选章节
                in_optional_section = False
                optional_section_level = 0
            continue

        # 检查未完成任务
        unchecked_match = re.match(unchecked_pattern, line)
        if unchecked_match:
            task_text = unchecked_match.group(1)
            if in_optional_section or _is_optional_task(line):
                optional_tasks.append(line.strip())
            else:
                required_unchecked.append(line.strip())
            continue

        # 检查已完成任务
        checked_match = re.match(checked_pattern, line)
        if checked_match:
            task_text = checked_match.group(1)
            if in_optional_section or _is_optional_task(line):
                optional_tasks.append(line.strip())
            else:
                required_checked.append(line.strip())

    return required_unchecked, required_checked, optional_tasks


def _get_file_mtime(doc_path: str) -> float:
    """获取文件修改时间"""
    try:
        return Path(doc_path).stat().st_mtime
    except Exception:
        return 0


def check_remaining_tasks(doc_path: str, use_cache: bool = True) -> Dict:
    """
    检查markdown文档中的任务进度（排除可选任务）

    优化4.1: 使用 LRU Cache + 文件修改时间检测，避免重复解析

    Args:
        doc_path: markdown文档路径
        use_cache: 是否使用缓存（默认True）

    Returns:
        dict: {
            "has_remaining": bool,  # 是否还有未完成的必选任务
            "total": int,           # 必选任务总数
            "completed": int,       # 已完成的必选任务数
            "remaining": int,       # 剩余的必选任务数
            "optional": int         # 可选任务数（不计入完成率）
        }
    """
    global _cache, _cache_timestamps

    try:
        doc_file = Path(doc_path)
        if not doc_file.exists():
            return {
                "has_remaining": False,
                "total": 0,
                "completed": 0,
                "remaining": 0,
                "optional": 0,
                "error": f"文档不存在: {doc_path}"
            }

        # 优化4.1: 检查缓存
        if use_cache and doc_path in _cache:
            cache_time = _cache_timestamps.get(doc_path, 0)
            file_mtime = _get_file_mtime(doc_path)

            # 如果缓存未过期且文件未修改，返回缓存结果
            if (time.time() - cache_time < CACHE_TTL) and (file_mtime <= cache_time):
                return _cache[doc_path]

        # 读取文档内容
        content = doc_file.read_text(encoding='utf-8')

        # 解析任务，区分必选和可选
        required_unchecked, required_checked, optional_tasks = _parse_tasks_with_optional_filter(content)

        total = len(required_unchecked) + len(required_checked)
        completed = len(required_checked)
        remaining = len(required_unchecked)
        optional = len(optional_tasks)

        result = {
            "has_remaining": remaining > 0,
            "total": total,
            "completed": completed,
            "remaining": remaining,
            "optional": optional
        }

        # 更新缓存
        _cache[doc_path] = result
        _cache_timestamps[doc_path] = time.time()

        return result

    except Exception as e:
        return {
            "has_remaining": False,
            "total": 0,
            "completed": 0,
            "remaining": 0,
            "optional": 0,
            "error": str(e)
        }


def clear_cache(doc_path: str = None) -> None:
    """
    清除缓存

    Args:
        doc_path: 如果指定，只清除该文档的缓存；否则清除所有缓存
    """
    global _cache, _cache_timestamps

    if doc_path:
        _cache.pop(doc_path, None)
        _cache_timestamps.pop(doc_path, None)
    else:
        _cache.clear()
        _cache_timestamps.clear()


def get_task_progress_summary(doc_path: str) -> str:
    """
    获取任务进度摘要字符串

    Args:
        doc_path: markdown文档路径

    Returns:
        str: 进度摘要，如 "3/10 completed (7 remaining, 5 optional excluded)"
    """
    result = check_remaining_tasks(doc_path)

    if "error" in result:
        return f"Error: {result['error']}"

    if result["total"] == 0 and result.get("optional", 0) == 0:
        return "No tasks found in document"

    optional_info = ""
    if result.get("optional", 0) > 0:
        optional_info = f", {result['optional']} optional excluded"

    return f"{result['completed']}/{result['total']} completed ({result['remaining']} remaining{optional_info})"
