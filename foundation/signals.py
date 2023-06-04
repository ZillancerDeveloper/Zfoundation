from allauth.socialaccount.models import SocialAccount
from django.db.models.signals import post_save
from django.dispatch import receiver

from foundation.models import User
from foundation.utils.notifications import welcome_email_notification


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
