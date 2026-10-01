from fastapi import status as http_status


class ApplicationError(Exception):
    def __init__(self, code: str, message: str, status: int) -> None:
        self.code = code
        self.message = message
        self.status = status
        super().__init__(message)


class InvalidInputError(ApplicationError):
    def __init__(self, message: str) -> None:
        super().__init__("invalid_parameters", message, http_status.HTTP_422_UNPROCESSABLE_CONTENT)
