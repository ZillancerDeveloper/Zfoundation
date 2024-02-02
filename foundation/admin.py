from constance import config
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from mptt.admin import MPTTModelAdmin

from foundation.models import (
    CurrencyMaster,
    CurrencyRate,
    User,
    UserAuthenticationOption,
    UserInfo,
    UserType,
    Menu,
    MenuAction,
    UserMenuSecurity,
    UsersMenuPermission,
    UserTypeMenuPermission,
)

admin.site.register(Menu, MPTTModelAdmin)
admin.site.register(MenuAction)


class BaseAdmin(admin.ModelAdmin):
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")


class UserTypeMenuPermissionInlineAdmin(admin.TabularInline):
    model = UserTypeMenuPermission
    extra = 1


@admin.register(UserType)
class UserType(BaseAdmin):
    inlines = [UserTypeMenuPermissionInlineAdmin]


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


class UsersMenuPermissionInlineAdmin(admin.TabularInline):
    model = UsersMenuPermission
    extra = 1


@admin.register(UserMenuSecurity)
class UserMenuSecurityAdmin(BaseAdmin):
    model = UserMenuSecurity
    inlines = [
        UsersMenuPermissionInlineAdmin,
    ]


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    inlines = [
        UserInfoInlineAdmin,
        UserAuthenticationOptionInlineAdmin,
    ]

    search_fields = [
        "email",
    ]
    list_display = ["email", "name", "is_active", "is_staff", "user_type"]
    list_display_links = ["email", "is_active", "is_staff"]
    list_filter = ("is_active", "is_staff", "is_superuser")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Personal info",
            {"fields": ("name", "user_type")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )

    def BE_AWARE_NO_WARNING_clear_tokens_and_delete(self, request, queryset):
        users = queryset.values("id")
        OutstandingToken.objects.filter(user__id__in=users).delete()
        queryset.delete()

    actions = ["BE_AWARE_NO_WARNING_clear_tokens_and_delete"]


@admin.register(CurrencyMaster)
class CurrencyMasterAdmin(BaseAdmin):
    list_display = ["currency_name", "currency_code", "currency_symbol", "default"]


@admin.register(CurrencyRate)
class CurrencyRateAdmin(BaseAdmin):
    list_display = [
        "currency_from",
        "currency_to",
        "buy_rate",
        "sell_rate",
        "effective_date",
    ]


admin.site.site_title = config.SITE_NAME
admin.site.site_header = config.SITE_NAME
