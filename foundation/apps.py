from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FoundationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "foundation"
    verbose_name = _("Foundation")

    def ready(self):
        import foundation.signals
