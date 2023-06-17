Installation
============

1. Install package:

.. code-block:: python

    pip install git+https://github.com/ZillancerDeveloper/Zfoundation.git

.. note:: As this package is a private package. You have to provide the github username and personal access token when trying to install. The username and access token will be provided by the Author.

2. Add related apps to INSTALLED_APPS in your django settings.py:

.. code-block:: python

    INSTALLED_APPS = (
        "constance",
        "constance.backends.database",
        ...,
        "rest_framework",
        "rest_framework_simplejwt",
        "rest_framework_simplejwt.token_blacklist",
        "rest_framework.authtoken",
        "dj_rest_auth",
        "allauth",
        "allauth.account",
        "allauth.socialaccount",
        "allauth.socialaccount.providers.google",
        "allauth.socialaccount.providers.apple",
        "django_filters",
        "phonenumber_field",
        "corsheaders",
        "django_celery_results",
        "django_cleanup.apps.CleanupConfig",
        "drf_spectacular",
        "foundation",
    )


3. Add cors middleware:

.. code-block:: python

    MIDDLEWARE = [
        ...,
        "corsheaders.middleware.CorsMiddleware",
        ...,
    ]

4. Import dependencies

.. code-block:: python

    from datetime import timedelta
    from .config import *


5. Add cors origins:

.. code-block:: python
    
    CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS")
    CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS")


6. Add rest framework:

.. code-block:: python

    REST_FRAMEWORK = {
        "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
        "DEFAULT_AUTHENTICATION_CLASSES": (
            "dj_rest_auth.jwt_auth.JWTCookieAuthentication",
        ),
        "DEFAULT_PAGINATION_CLASS": "foundation.api.pagination.CustomPageNumberPagination",
        "PAGE_SIZE": 50,
        "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    }


6. Add simple jwt:

.. code-block:: python

    SIMPLE_JWT = {
        "ACCESS_TOKEN_LIFETIME": timedelta(days=60),
        "REFRESH_TOKEN_LIFETIME": timedelta(days=15),
        "ROTATE_REFRESH_TOKENS": True,
        "BLACKLIST_AFTER_ROTATION": True,
        "UPDATE_LAST_LOGIN": True,
    }


6. Add spectacular settings:

.. code-block:: python

    SPECTACULAR_SETTINGS = {
        "TITLE": "Foundation Demo App API",
        "DESCRIPTION": "Foundation Demo Service application",
        "VERSION": "1.0.0",
        "SERVE_INCLUDE_SCHEMA": False,
        "COMPONENT_SPLIT_REQUEST": True,
    }


7. Add rest auth:

.. code-block:: python

    REST_AUTH = {
        "USE_JWT": True,
        "JWT_AUTH_COOKIE": "access",
        "JWT_AUTH_REFRESH_COOKIE": "refresh",
        "JWT_AUTH_HTTPONLY": False,
    }


8. Add custom rest auth serializers:

.. code-block:: python

    REST_AUTH_SERIALIZERS = {
        "TOKEN_SERIALIZER": "foundation.api.serializers.CustomTokenSerializer",  # import path to CustomTokenSerializer defined above.
    }


9. Add others settings:

.. code-block:: python

    AUTH_USER_MODEL = "foundation.User"

    ACCOUNT_EMAIL_VERIFICATION = "none"
    ACCOUNT_AUTHENTICATION_METHOD = "email"
    ACCOUNT_EMAIL_REQUIRED = True
    ACCOUNT_USER_MODEL_USERNAME_FIELD = None
    ACCOUNT_USERNAME_REQUIRED = False
    ACCOUNT_UNIQUE_EMAIL = True

    FRONTEND_DOMAIN = env("FRONTEND_DOMAIN")
    RESET_PASSWORD_LINK = env("RESET_PASSWORD_LINK")
    CALLBACK_URL = env("CALLBACK_URL")


10. Add socialaccount prividers:

.. code-block:: python

    SOCIALACCOUNT_PROVIDERS = {
        "google": {
            "APP": {
                "client_id": "GOOGLE_OAUTH_CLIENT_ID",
                "secret": "GOOGLE_OAUTH_SECRET",
            },
            "SCOPE": [
                "profile",
                "email",
                "phone",
            ],
            "AUTH_PARAMS": {
                "access_type": "online",
            },
        },
        "apple": {
            "APP": {
                "client_id": "APPLE_CLIENT_ID",
                "secret": "KEY_ID",
                "key": "ABCDEF",
                "certificate_key": "CERTIFICATE_KEY",
            }
        },
    }
    

11. Add celery settings:

.. code-block:: python

    REDIS_URL = env("REDIS_URL")

    CELERY_BROKER_URL = REDIS_URL    # "redis://localhost:6379"
    CELERY_ACCEPT_CONTENT = {"application/json"}
    CELERY_RESULT_SERIALIZER = "json"
    CELERY_TASK_SERIALIZER = "json"
    CELERY_TIMEZONE = "Asia/Dubai"
    CELERY_RESULT_BACKEND = "django-db"
    

12. Add smtp settings:

.. code-block:: python

    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_USE_TLS = True
    EMAIL_HOST = "smtp.gmail.com"
    EMAIL_PORT = 587
    

13. Add twilio settings:

.. code-block:: python

    TWILIO_ACCOUNT_SID = env("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = env("TWILIO_AUTH_TOKEN")
    TWILIO_FROM_WHATSAPP_NUMBER = env("TWILIO_FROM_WHATSAPP_NUMBER")
    

14. Make the user type field required/optional in sign up form:

.. code-block:: python

    SIGN_UP_USER_TYPE_REQUIRED = False
    SIGN_UP_USER_TYPE_ALLOW_NULL = False


Custom user serialzier (optional)
-----------------------

1. If you want write custom ``USER_SERIALIZER`` to your django settings.py

.. code-block:: python

    USER_INFO_SERIALIZERS = {
        "USER_SERIALIZER": "api.master.serializers.CustomUserSerializer"   # Replace with your own serializer
    }
    