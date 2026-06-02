import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_password_reset_email(self, email: str, reset_link: str):
    """Send the password-reset email off the request thread.

    Retries a few times on transient SMTP failures. If every retry is exhausted
    the failure is logged at ERROR (not swallowed) so it is visible in monitoring.
    """
    try:
        send_mail(
            subject="Reset your password",
            message=f"Click the link to reset your password:\n{reset_link}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
        )
    except Exception as exc:
        # Last attempt — give up loudly instead of failing silently.
        if self.request.retries >= self.max_retries:
            logger.error(
                "Password-reset email to %s permanently failed after %d attempts: %s",
                email,
                self.max_retries + 1,
                exc,
            )
            raise

        logger.warning(
            "Password-reset email to %s failed (attempt %d/%d), retrying: %s",
            email,
            self.request.retries + 1,
            self.max_retries + 1,
            exc,
        )
        raise self.retry(exc=exc) from exc
