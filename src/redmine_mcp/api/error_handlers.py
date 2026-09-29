from fastapi import Request
from fastapi.responses import JSONResponse

from redmine_mcp.common.errors import ApplicationError


async def application_error(request: Request, exc: ApplicationError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status, content={"error": {"code": exc.code, "message": exc.message}}
    )
