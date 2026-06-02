"""Development settings — local convenience, never for production.

Selected when ``DJANGO_ENV`` is unset or ``dev``. Also the settings the test
suite and mypy pin to explicitly.
"""

from .base import *  # noqa: F401,F403

# Debug on by default locally; still overridable via the DEBUG env var.
DEBUG = env.bool("DEBUG", default=True)  # noqa: F405

# Be permissive about hosts in local/dev so runserver and tooling just work.
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "0.0.0.0"])  # noqa: F405
