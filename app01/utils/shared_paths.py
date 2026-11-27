from pathlib import PureWindowsPath,PurePosixPath

from django.conf import settings
from django.core.exceptions import ValidationError

def normalize_relative_share_path(value):
    """规范化共享盘相对路径，并拒绝绝对路径和目录回退"""
    raw_path=(value or "").strip()
    normalized=raw_path.replace("\\","/")

    # Windows 路径规则解析，能按 Windows 规则识别反斜杠 \、盘符和 UNC 路径
    windows_path = PureWindowsPath(raw_path)
    # POSIX（Linux/macOS）路径规则解析
    posix_path = PurePosixPath(normalized)

    # 仅接收相对于共享盘根目录的路径，拒绝盘符、根路径和目录回退。
    if (
        not normalized
        or windows_path.is_absolute()
        or windows_path.drive
        or posix_path.is_absolute()
        or ".." in posix_path.parts
        or posix_path == PurePosixPath(".")
    ):
        raise ValidationError("请输入安全共享盘相对路径")
    # as_posix()返回使用 / 分隔符的字符串。
    return posix_path.as_posix()

def build_display_share_path(share_root,relative_path):
    """将共享盘配置键和数据库中的相对路径拼成展示的完整路径"""
    root=settings.PROJECT_SHARE_ROOT.get(share_root,"")
    # 本地没有配置共享盘根目录时，仍返回可识别的逻辑路径
    if not root :
        return f"{share_root}:/{relative_path}"

    path=PureWindowsPath(root)
    for part in relative_path.replace("\\","/").split("/"):
        if part:
            path /=part
    return str(path)