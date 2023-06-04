import random
from datetime import timedelta

from constance import config
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from twilio.rest import Client

from foundation.models import User, UserAuthenticationOption
from foundation.utils.emails import send_email


def welcome_email_notification(user: User):
    to_email = user.email
    subject = f"Welcome to {config.SITE_NAME}"
    context = {
        "site_name": config.SITE_NAME,
        "user": user,
    }
    html_content = render_to_string("foundation/emails/welcome.html", context)

    send_email.delay(
        subject,
        "A curated message for sending welcome notification.",
        html_content,
        mail_to=[to_email],
    )


def send_whatsapp_notification(user_whatsapp_number, message):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    client.messages.create(
        from_=f"whatsapp:{settings.TWILIO_FROM_WHATSAPP_NUMBER}",
        body=message,
        to=f"whatsapp:{user_whatsapp_number}",
    )

    return "Great! Expect a message..."


def generate_otp(user: User, otp_method: str) -> None:
    otp = random.randint(100000, 999999)

    if otp_method == "email":
        try:
            if user.email:
                recipient_list = [
                    user.email,
                ]

                # Save OTP to User model
                expire_at = timezone.now() + timedelta(minutes=5)
                UserAuthenticationOption.objects.filter(user=user).update(
                    otp=otp, otp_expired_at=expire_at
                )

                # Send Email to user
                context = {
                    "user": user,
                    "otp_code": otp,
                    "site_name": config.SITE_NAME,
                }
                subject = "Your single-use OTP"
                html_content = render_to_string(
                    "foundation/emails/otp_message.html", context
                )

                send_email.delay(
                    subject,
                    "A curated message based on the design the otp send.",
                    html_content,
                    mail_to=recipient_list,
                )
        except Exception as err:
            raise ValueError(err)

    elif otp_method == "voice_call":
        pass

    elif otp_method == "sms":
        pass
