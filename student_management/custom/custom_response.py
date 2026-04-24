from rest_framework.response import Response


class CustomResponse(Response):
    def __init__(
        self,
        data=None,
        message: str = "",
        success: bool = True,
        status: int = 200,
        headers=None,
        errors=None,
        code: str = "success",
        **kwargs,
    ):
        payload = {
            "data": data,
            "message": message,
            "success": success,
            "errors": errors,
            "code": code,
            "status": status,
            **kwargs,
        }

        super().__init__(data=payload, status=status, headers=headers)
