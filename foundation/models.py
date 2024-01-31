from __future__ import unicode_literals

from datetime import datetime
from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower
from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey
from phonenumber_field.modelfields import PhoneNumberField

from foundation.managers import CustomUserManager
from foundation.utils.base import get_current_user


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        "foundation.User",
        on_delete=models.SET_NULL,
        null=True,
        editable=False,
        related_name="%(class)s_created",
    )
    updated_by = models.ForeignKey(
        "foundation.User",
        on_delete=models.SET_NULL,
        null=True,
        editable=False,
        related_name="%(class)s_updated",
    )

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and user.is_authenticated:
            self.updated_by = user
            if not self.id:
                self.created_by = user
        super(BaseModel, self).save(*args, **kwargs)

    class Meta:
        abstract = True


class CurrencyMaster(BaseModel):
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


class UserType(BaseModel):
    name = models.CharField(max_length=50, verbose_name=_("Name"), unique=True)
    visible_in_signup = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = _("User Type")
        verbose_name_plural = _("User Type")
        ordering = ("-id",)
        constraints = [models.UniqueConstraint(Lower("name"), name="unique_name")]


class User(AbstractUser):
    LANGUAGES = (
        ('en', _('English')),
        ('fr', _('French')),
        ('de', _('German')),
        ('it', _('Italian'))
    )
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
    language = models.CharField(max_length=150,null=True,blank=True,choices=LANGUAGES, default="English")

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


class CurrencyRate(BaseModel):
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


class Menu(MPTTModel, BaseModel):
    name = models.CharField(max_length=50, verbose_name=_("Name"), unique=True)
    slug = models.SlugField(max_length=100, verbose_name=_("Slug"), editable=False)
    parent = TreeForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        verbose_name=_("Parent"),
    )
    icon = models.ImageField(
        verbose_name=_("Icon"), upload_to="menu/icon/", blank=True, null=True
    )
    url = models.URLField(verbose_name=_("URL"), blank=True, null=True)
    order = models.IntegerField(verbose_name=_("Order"), default=0)
    visible_for_authenticated = models.BooleanField(
        verbose_name=_("Visible for authenticated"), default=True
    )
    visible_for_anonymous = models.BooleanField(
        verbose_name=_("Visible for anonymous"), default=False
    )

    def __str__(self) -> str:
        return self.name

    class Meta:
        ordering = ("order",)
        verbose_name = _("Menu")
        verbose_name_plural = _("Menu")

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        return super().save(*args, **kwargs)


class MenuAction(BaseModel):
    action = models.CharField(max_length=10, verbose_name=_("Action"), unique=True)
    icon = models.ImageField(
        verbose_name=_("Icon"), upload_to="menu_items/icon/", blank=True, null=True
    )
    class_name = models.CharField(
        max_length=10,
        verbose_name=_("Class name"),
        blank=True,
        null=True,
        help_text=_("Use for HTML class name."),
    )

    def __str__(self) -> str:
        return self.action

    class Meta:
        ordering = ("id",)
        verbose_name = _("Menu Action")
        verbose_name_plural = _("Menu Action")


class UserTypeMenuPermission(BaseModel):
    user_type = models.ForeignKey(
        UserType,
        on_delete=models.CASCADE,
        verbose_name=_("Select user type"),
        related_name="usertype_menu_set",
    )
    menu = models.ForeignKey(
        Menu, on_delete=models.CASCADE, verbose_name=_("Select menu")
    )
    menu_action = models.ManyToManyField(
        MenuAction,
        related_name="user_type_menu_action_set",
        verbose_name=_("Select menu actions"),
    )

    def __str__(self) -> str:
        return f"{self.user_type} - {self.menu}"

    class Meta:
        ordering = ("-id",)
        unique_together = ("user_type", "menu")
        verbose_name = _("User Type Menu Permission")
        verbose_name_plural = _("User Type Menu Permission")


class UserMenuSecurity(BaseModel):
    users = models.ManyToManyField(User, verbose_name=_("Select users"))

    # def __str__(self) -> str:
    #     return f"{self.user} - {self.menu}"

    class Meta:
        ordering = ("-id",)
        verbose_name = _("User Menu Security")
        verbose_name_plural = _("User Menu Security")


class UsersMenuPermission(BaseModel):
    users_menu = models.ForeignKey(
        UserMenuSecurity,
        models.PROTECT,
        verbose_name=_("Select users"),
        related_name="users_menu_set",
    )
    menu = models.ForeignKey(
        Menu, on_delete=models.CASCADE, verbose_name=_("Select menu")
    )
    menu_action = models.ManyToManyField(
        MenuAction,
        related_name="user_menu_action_set",
        verbose_name=_("Select menu actions"),
    )

    # def __str__(self) -> str:
    #     return f"{self.user} - {self.menu}"

    class Meta:
        ordering = ("-id",)
        verbose_name = _("Users Menu Permission")
        verbose_name_plural = _("Users Menu Permission")
