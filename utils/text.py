from typing import Optional


def truncate_with_ellipsis(s: Optional[str], limit: int) -> str:
    if not s: return ""
    return s if len(s) <= limit else s[: max(0, limit - 3)] + "..."
