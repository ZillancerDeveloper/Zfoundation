from __future__ import unicode_literals

from datetime import datetime
from decimal import Decimal
from typing import Iterable, Optional

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from foundation.managers import CustomUserManager


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CurrencyMaster(models.Model):
    currency_name = models.CharField(max_length=50, verbose_name=_("Currency Name"))
    currency_code = models.CharField(max_length=20, verbose_name=_("Currency Code"))
    currency_symbol = models.CharField(
        max_length=5, verbose_name=_("Currency Symbol"), blank=True, null=True
    )
    default = models.BooleanField(default=False, verbose_name=_("Default"))

    def __str__(self) -> str:
        return self.currency_name

    class Meta:
        verbose_name = _("Currency Master")
        verbose_name_plural = _("Currency Master")
        ordering = ("id",)

    def validate_unique(self, *args, **kwargs):
        super().validate_unique(*args, **kwargs)
        if (
            self.default
            and self.__class__.objects.exclude(id=self.id).filter(default=True).exists()
        ):
            raise ValidationError(
                message="One default currency already exists.",
                code="unique",
            )

    @classmethod
    def get_default_pk(cls):
        try:
            return cls.objects.get(default=True).pk
        except cls.DoesNotExist:
            return ""


class UserType(models.Model):
    name = models.CharField(max_length=50, verbose_name=_("Name"))

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = _("User Type")
        verbose_name_plural = _("User Type")
        ordering = ("id",)


class User(AbstractUser):
    username = None
    first_name = None
    last_name = None
    name = models.CharField(verbose_name=_("Name"), max_length=150, blank=True)
    email = models.EmailField(verbose_name=_("Email"), unique=True)
    user_type = models.ForeignKey(
        UserType,
        verbose_name=_("User Type"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self) -> str:
        return self.email


class UserInfo(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, verbose_name=_("User"), related_name="userinfo"
    )
    phone_number1 = PhoneNumberField(verbose_name=_("Phone Number 1"))
    phone_number2 = PhoneNumberField(
        verbose_name=_("Phone Number 2"),
        help_text=_("For whats app"),
        blank=True,
        null=True,
    )
    base_currency = models.ForeignKey(
        CurrencyMaster,
        on_delete=models.CASCADE,
        default=CurrencyMaster.get_default_pk,
        verbose_name=_("Base Currency"),
    )


class UserAuthenticationOption(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, verbose_name=_("User"), related_name="userauth"
    )
    two_step_verification = models.BooleanField(
        default=False, verbose_name=_("Two Step Verification")
    )
    device_authenticator = models.BooleanField(
        default=False, verbose_name=_("Device Authenticator")
    )
    otp_verification = models.BooleanField(
        default=False, verbose_name=_("OTP Verification")
    )
    otp = models.CharField(max_length=10, blank=True, null=True, verbose_name=_("OTP"))
    otp_expired_at = models.DateTimeField(
        blank=True, null=True, verbose_name=_("Expired At")
    )

    def clean(self) -> None:
        if self.two_step_verification:
            if not self.device_authenticator and not self.otp_verification:
                raise ValidationError(
                    {"two_step_verification": "At least one step should be select."}
                )

        return super().clean()


class CurrencyRate(models.Model):
    currency_from = models.ForeignKey(
        CurrencyMaster,
        on_delete=models.CASCADE,
        verbose_name=_("Currency From"),
        related_name="curr_master_from",
    )
    currency_to = models.ForeignKey(
        CurrencyMaster,
        on_delete=models.CASCADE,
        verbose_name=_("Currency To"),
        related_name="curr_master_to",
    )
    buy_rate = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal("0.0000"),
        verbose_name=_("Buy Rate"),
    )
    sell_rate = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal("0.0000"),
        verbose_name=_("Sell Rate"),
    )
    effective_date = models.DateTimeField(
        default=datetime.now, verbose_name=_("Effective Date")
    )

    def __str__(self) -> str:
        return f"{self.currency_from} - {self.currency_to}"

    class Meta:
        ordering = ("effective_date",)
        get_latest_by = ("effective_date",)
        verbose_name = _("Currency Rate")
        verbose_name_plural = _("Currency Rate")
