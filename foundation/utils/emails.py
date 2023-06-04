import time

from celery import shared_task
from constance import config
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.mail.backends.smtp import EmailBackend


@shared_task(serializer="json")
def send_email(
    subject,
    message,
    html_content=None,
    mail_from=None,
    mail_to=None,
    bcc=None,
    attachments=None,
    cc=None,
    reply_to=None,
):
    """Send email function"""

    time.sleep(20)  # for check that sending email process runs in background

    try:
        backend = EmailBackend(
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=config.EMAIL,
            password=config.APP_PASSWORD,
            use_tls=settings.EMAIL_USE_TLS,
            fail_silently=False,
        )

        if mail_from is None:
            mail_from = config.EMAIL

        mail = EmailMultiAlternatives(
            subject=subject,
            body=message,
            from_email=mail_from,
            to=mail_to,
            bcc=bcc,
            connection=backend,
            cc=cc,
            reply_to=reply_to,
        )

        if html_content:
            mail.attach_alternative(html_content, "text/html")

        if attachments:
            for attachment in attachments:
                mail.attach(attachment.name, attachment.read(), attachment.content_type)

        mail.send()

        return "Done"
    except Exception as err:
        raise ValueError(err)
