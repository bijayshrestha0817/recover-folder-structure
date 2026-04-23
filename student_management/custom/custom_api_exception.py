from typing import Any

from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError


class CustomAPIException(ValidationError):
    status_code: int = status.HTTP_400_BAD_REQUEST
    default_code: str = "error"

    def __init__(self, detail: Any = None, status_code: int | None = None):
        if status_code is not None:
            self.status_code = int(status_code)

        if detail is None:
            detail = []

        elif isinstance(detail, str):
            detail = [detail]

        elif isinstance(detail, list | dict):
            detail = detail

        super().__init__(detail)


class CustomException(APIException):
    status_code: int = status.HTTP_400_BAD_REQUEST
    default_code: str = "validation_error"

    def __init__(
        self,
        data: Any = None,
        message: str = "",
        status_code: int = 400,
        errors: Any = None,
        code: str = "validation_error",
        **kwargs,
    ):
        self.status_code = int(status_code)

        self.payload = {
            "data": data,
            "message": message,
            "success": False,
            "errors": errors,
            "code": code,
            **kwargs,
        }

        super().__init__(detail=message)
