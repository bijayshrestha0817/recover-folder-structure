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
        # Surface the first concrete field error (e.g. "This password is too
        # common.") instead of a generic message, while keeping the full error
        # map in ``errors`` for the client to map back to fields.
        message, errors = _first_error_message(detail), detail

    response.data = {
        "data": None,
        "message": message,
        "success": False,
        "errors": errors,
        "code": getattr(exc, "default_code", "error"),
        "status": response.status_code,
    }
    return response


def _first_error_message(detail, fallback="Request failed."):
    """Pull the first human-readable error string out of a DRF error payload.

    DRF validation errors are nested as ``{field: [messages]}`` (and lists can
    themselves hold dicts for nested serializers). Walk the structure depth-first
    and return the first string found.
    """
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list):
        for item in detail:
            message = _first_error_message(item, fallback=None)
            if message:
                return message
    elif isinstance(detail, dict):
        for value in detail.values():
            message = _first_error_message(value, fallback=None)
            if message:
                return message
    return fallback
