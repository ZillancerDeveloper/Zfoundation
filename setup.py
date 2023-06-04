from setuptools import setup

setup(install_requires=[
    "djangorestframework",
    "django-filter",
    "django-constance[database]",
    "django-phonenumber-field",
    "phonenumbers",
    "djangorestframework-simplejwt",
    "redis",
    "celery",
    "django-celery-results",
    "django-allauth",
    "twilio",
    "dj-rest-auth==2.2.5",
    "django-cors-headers",
    "drf_spectacular",
    "django-cleanup",
])
