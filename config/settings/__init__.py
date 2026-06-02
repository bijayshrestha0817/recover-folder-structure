"""Environment dispatcher.

Keeps ``DJANGO_SETTINGS_MODULE=config.settings`` valid everywhere (manage.py,
wsgi, asgi, celery) while choosing dev vs prod at import time via ``DJANGO_ENV``.

  DJANGO_ENV=dev   (default) -> config/settings/dev.py
  DJANGO_ENV=prod            -> config/settings/prod.py

The test suite and mypy bypass this by pointing at ``config.settings.dev``
directly, so their config never depends on the ambient ``DJANGO_ENV``.
"""

import os

from environ import Env

# Load .env first so DJANGO_ENV may be set there as well as in the real environment.
Env.read_env()

DJANGO_ENV = os.environ.get("DJANGO_ENV", "dev").strip().lower()

if DJANGO_ENV == "prod":
    from .prod import *  # noqa: F401,F403
elif DJANGO_ENV == "dev":
    from .dev import *  # noqa: F401,F403
else:
    raise ImportError(f"Unknown DJANGO_ENV={DJANGO_ENV!r}; expected 'dev' or 'prod'.")
