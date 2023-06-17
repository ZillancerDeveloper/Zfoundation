Configuration
============

1. Add ``config.py`` in your project folder, which is the same level of ``settings.py``:

.. code-block:: python

    from django.utils.translation import gettext_lazy as _

    CONSTANCE_IGNORE_ADMIN_VERSION_CHECK = True
    CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"

    CONSTANCE_ADDITIONAL_FIELDS = {
        "image_field": ["django.forms.ImageField", {"required": False}]
    }

    CONSTANCE_CONFIG = {
        "SITE_NAME": ("Foundation Demo App", _("Website title")),
        "SITE_DESCRIPTION": ("", _("Website description")),
        "LOGO_IMAGE": ("", _("Company logo"), "image_field"),
        # Email settings
        "EMAIL": ("admin@example.com", _("Email sender")),
        "APP_PASSWORD": ("123456", _("Sender app password")),
    }

    CONSTANCE_CONFIG_FIELDSETS = (
        (
            _("General Options"),
            {
                "fields": (
                    "SITE_NAME",
                    "SITE_DESCRIPTION",
                    "LOGO_IMAGE",
                ),
                "collapse": False,
            },
        ),
        (
            _("Email Options"),
            {
                "fields": (
                    "EMAIL",
                    "APP_PASSWORD",
                ),
                "collapse": True,
            },
        ),
    )


2. Add ``celery.py`` in your project folder, which is the same level of ``settings.py``:

.. code-block:: python

    from __future__ import absolute_import, unicode_literals

    import os

    from celery import Celery

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "z_foundation.settings")

    app = Celery("foundation")
    app.config_from_object("django.conf:settings", namespace="CELERY")

    app.conf.enable_utc = False

    app.conf.update(timezone="Asia/Dhaka")

    app.autodiscover_tasks()


3. Add in the ``__init__.py`` in your project folder, which is the same level of ``settings.py``:

.. code-block:: python

    # This will make sure the app is always imported when
    # Django starts so that shared_task will use this app.

    from .celery import app

    __all__ = ("app",)


4. Add in the ``urls.py`` in your project folder, which is the same level of ``settings.py``:

.. code-block:: python

    from django.contrib import admin
    from django.urls import path, include
    from allauth.socialaccount.views import signup
    from django.conf import settings
    from django.conf.urls.static import static 
    
    from drf_spectacular.views import (
        SpectacularAPIView,
        SpectacularRedocView,
        SpectacularSwaggerView,
    )

    urlpatterns = (
        [
            path("admin/", admin.site.urls),
            # APPs endpints
            path("foundation/", include("foundation.api.urls", namespace="foundation-api")),
            ....,
            path("signup/", signup, name="socialaccount_signup"),
        ]
        + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
        + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    )

    # Schema URLs
    urlpatterns += [
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        path(
            "api/schema/swagger-ui/",
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="swagger-ui",
        ),
        path(
            "api/schema/redoc/",
            SpectacularRedocView.as_view(url_name="schema"),
            name="redoc",
        ),
    ]

4. Migrate your database

.. code-block:: python

    python manage.py migrate


You're good to go now!

