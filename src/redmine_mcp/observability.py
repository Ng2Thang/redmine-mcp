import logging
from contextvars import ContextVar

request_id: ContextVar[str] = ContextVar("request_id", default="-")


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id.get()
        return True


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)s %(name)s request_id=%(request_id)s %(message)s",
    )
    logging.getLogger().setLevel(level.upper())
    for handler in logging.getLogger().handlers:
        if not any(isinstance(entry, RequestContextFilter) for entry in handler.filters):
            handler.addFilter(RequestContextFilter())
    for name in ("httpx", "httpcore", "fastapi_mcp"):
        logging.getLogger(name).setLevel(logging.WARNING)
