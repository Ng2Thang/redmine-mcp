"""Limits for one upstream read, distinct from connection-pool configuration."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReadPolicy:
    deadline_seconds: float = 60
    max_response_bytes: int = 10 * 1024 * 1024
    max_binary_bytes: int = 5 * 1024 * 1024
    max_query_pages: int = 10
    public_url: str | None = None
