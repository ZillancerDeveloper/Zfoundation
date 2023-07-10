from allauth.socialaccount.models import SocialAccount
from django.db.models.signals import post_save
from django.conf import settings
from django.dispatch import receiver

from foundation.models import User
from foundation.utils.notifications import welcome_email_notification
from constance.signals import config_updated
import os


@receiver(config_updated)
def constance_updated(sender, key, old_value, new_value, **kwargs):
    if key == "LOGO_IMAGE":
        file_path = f"{settings.MEDIA_ROOT}\{old_value}"

        if os.path.isfile(file_path):
            os.remove(file_path)


# call function when click on save social account
@receiver(post_save, sender=SocialAccount)
def send_email_notification(sender, instance, created, **kwargs):
    if created:
        # save user name from extra data
        user = User.objects.get(id=instance.user.id)
        user.name = instance.extra_data.get("name")
        user.save()
        # Send welcome mail
        welcome_email_notification(user)
