import logging

from fastapi import Request
from fastapi import status as http_status
from fastapi.responses import JSONResponse

from redmine_mcp.common import ApplicationError, InvalidInputError
from redmine_mcp.observability import request_id

logger = logging.getLogger(__name__)


async def application_error(request: Request, exc: ApplicationError) -> JSONResponse:
    logger.warning("request_failed code=%s status=%s", exc.code, exc.status)
    if isinstance(exc, InvalidInputError):
        return JSONResponse(
            status_code=http_status.HTTP_422_UNPROCESSABLE_CONTENT, content={"detail": exc.message}
        )
    return JSONResponse(
        status_code=exc.status, content={"error": {"code": exc.code, "message": exc.message}}
    )


async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    # Exception strings and traceback locals can contain keys or upstream content.
    logger.error("request_failed code=internal_error exception_type=%s", type(exc).__name__)
    correlation = getattr(request.state, "request_id", request_id.get())
    return JSONResponse(
        status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": {"code": "internal_error", "message": "Internal server error"}},
        headers={"X-Request-ID": correlation} if correlation != "-" else {},
    )
