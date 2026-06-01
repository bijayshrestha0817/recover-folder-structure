from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_password_reset_email(self, email: str, reset_link: str):
    """Send the password-reset email off the request thread.

    Retries a few times on transient SMTP failures.
    """
    try:
        send_mail(
            subject="Reset your password",
            message=f"Click the link to reset your password:\n{reset_link}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
        )
    except Exception as exc:
        raise self.retry(exc=exc) from exc
