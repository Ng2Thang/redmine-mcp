from fastapi import status as http_status

from redmine_mcp.constants import codes as codes_text


class ApplicationError(Exception):
    def __init__(self, code: str, message: str, status: int) -> None:
        self.code = code
        self.message = message
        self.status = status
        super().__init__(message)


class InvalidInputError(ApplicationError):
    def __init__(self, message: str) -> None:
        super().__init__(
            codes_text.INVALID_PARAMETERS, message, http_status.HTTP_422_UNPROCESSABLE_CONTENT
        )
