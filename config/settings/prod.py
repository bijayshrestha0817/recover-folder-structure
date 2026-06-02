"""Production settings — hardened.

Selected when ``DJANGO_ENV=prod``. Layers HTTPS / HSTS / secure-cookie / content
hardening on top of ``base`` and removes the insecure dev defaults. Verify with::

    DJANGO_ENV=prod python manage.py check --deploy
"""

from .base import *  # noqa: F401,F403

# Never debug in production.
DEBUG = False

# No insecure fallback: a real secret and explicit hosts are required.
SECRET_KEY = env.str("SECRET_KEY")  # noqa: F405  -> raises if unset
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")  # noqa: F405  -> raises if unset

# --- HTTPS / transport security -------------------------------------------
# Redirect all HTTP to HTTPS (disable only if TLS is terminated elsewhere and
# the proxy already redirects). Trust the proxy's forwarded-proto header.
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)  # noqa: F405
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# HTTP Strict Transport Security — start conservative and raise once verified.
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=60 * 60 * 24 * 365)  # noqa: F405
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# --- Cookies ---------------------------------------------------------------
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True

# --- Content / header hardening -------------------------------------------
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# CSRF trusted origins (scheme required) — set from the env in deployment.
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])  # noqa: F405
