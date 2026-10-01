"""Auth text constants; no runtime dependencies.

Templates use named str.format arguments; log templates use logging placeholders.
"""

from typing import Final

INVALID_API_KEY: Final[str] = "Missing or invalid Redmine API key"

PERMISSION_DENIED: Final[str] = "Permission denied"

WRITE_ACCESS_DISABLED: Final[str] = "Write access is disabled"

__all__ = [
    "INVALID_API_KEY",
    "PERMISSION_DENIED",
    "WRITE_ACCESS_DISABLED",
]
