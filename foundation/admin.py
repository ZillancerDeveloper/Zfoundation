from constance import config
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

from foundation.models import (
    CurrencyMaster,
    CurrencyRate,
    User,
    UserAuthenticationOption,
    UserInfo,
    UserType,
)

admin.site.register(UserType)


class UserInfoInlineAdmin(admin.StackedInline):
    model = UserInfo


class UserAuthenticationOptionInlineAdmin(admin.StackedInline):
    model = UserAuthenticationOption
    fieldsets = (
        (
            None,
            {"fields": ("two_step_verification",)},
        ),
        (
            "Authentication Steps",
            {
                "fields": (
                    "device_authenticator",
                    "otp_verification",
                )
            },
        ),
        (
            None,
            {
                "fields": (
                    "otp",
                    "otp_expired_at",
                )
            },
        ),
    )


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    inlines = [UserInfoInlineAdmin, UserAuthenticationOptionInlineAdmin]

    search_fields = [
        "email",
    ]
    list_display = ["email", "name", "is_active", "is_staff", "user_type"]
    list_display_links = ["email", "is_active", "is_staff"]
    list_filter = ("is_active", "is_staff", "is_superuser")
    ordering = ("email",)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "email",
                    "password",
                    (
                        "user_type",
                        "is_staff",
                        "is_active",
                        "is_superuser",
                        "last_login",
                    ),
                )
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    (
                        "is_staff",
                        "is_active",
                    ),
                ),
            },
        ),
    )

    def BE_AWARE_NO_WARNING_clear_tokens_and_delete(self, request, queryset):
        users = queryset.values("id")
        OutstandingToken.objects.filter(user__id__in=users).delete()
        queryset.delete()

    actions = ["BE_AWARE_NO_WARNING_clear_tokens_and_delete"]


@admin.register(CurrencyMaster)
class CurrencyMasterAdmin(admin.ModelAdmin):
    list_display = ["currency_name", "currency_code", "currency_symbol", "default"]


@admin.register(CurrencyRate)
class CurrencyRateAdmin(admin.ModelAdmin):
    list_display = [
        "currency_from",
        "currency_to",
        "buy_rate",
        "sell_rate",
        "effective_date",
    ]


admin.site.site_title = config.SITE_NAME
admin.site.site_header = config.SITE_NAME