from rest_framework.views import exception_handler as drf_exception_handler

from student_management.custom.custom_api_exception import CustomException


def custom_exception_handler(exc, context):
    """Render every error through the same envelope as ``CustomResponse``.

    - ``CustomException`` carries a pre-built ``payload`` — surface it directly.
    - Any other DRF exception is normalized into the same shape so clients get a
      consistent ``{data, message, success, errors, code, status}`` body.
    """
    response = drf_exception_handler(exc, context)

    if response is None:
        return None

    if isinstance(exc, CustomException):
        response.data = {**exc.payload, "status": response.status_code}
        return response

    detail = response.data
    if isinstance(detail, dict) and "detail" in detail and len(detail) == 1:
        message, errors = str(detail["detail"]), None
    else:
        message, errors = "Request failed.", detail

    response.data = {
        "data": None,
        "message": message,
        "success": False,
        "errors": errors,
        "code": getattr(exc, "default_code", "error"),
        "status": response.status_code,
    }
    return response
