from typing import Any

from rest_framework import status
from rest_framework.exceptions import APIException


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
