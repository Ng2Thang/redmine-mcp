import logging

from fastapi import Request
from fastapi import status as http_status
from fastapi.responses import JSONResponse

from redmine_mcp.common import ApplicationError, InvalidInputError
from redmine_mcp.constants import api as api_text
from redmine_mcp.constants import codes as codes_text
from redmine_mcp.constants import logs as logs_text
from redmine_mcp.observability import debug_exception, request_id

logger = logging.getLogger(__name__)


async def application_error(request: Request, exc: ApplicationError) -> JSONResponse:
    logger.warning(logs_text.REQUEST_FAILED, exc.code, exc.status)
    debug_exception(logger, exc)
    if isinstance(exc, InvalidInputError):
        return JSONResponse(
            status_code=http_status.HTTP_422_UNPROCESSABLE_CONTENT, content={"detail": exc.message}
        )
    return JSONResponse(
        status_code=exc.status, content={"error": {"code": exc.code, "message": exc.message}}
    )


async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    # Exception strings and traceback locals can contain keys or upstream content.
    logger.error(logs_text.UNEXPECTED_ERROR, type(exc).__name__)
    debug_exception(logger, exc)
    correlation = getattr(request.state, "request_id", request_id.get())
    return JSONResponse(
        status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {"code": codes_text.INTERNAL_ERROR, "message": api_text.INTERNAL_SERVER_ERROR}
        },
        headers={"X-Request-ID": correlation} if correlation != "-" else {},
    )
