from dj_rest_auth.views import PasswordChangeView, PasswordResetConfirmView
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from api.foundation.views import (
    AppleLogin,
    CurrencyMasterViewSet,
    EmailSendView,
    GoogleLogin,
    LoginAPIView,
    LogoutView,
    OTPGenerateAPIView,
    OTPVerificationAPIView,
    PasswordResetView,
    RegistrationAPIView,
    UserTypeViewSet,
    UserViewSet,
    WhatsAPPView,
    google_token,
)

app_name = "api.foundation"

router = DefaultRouter()
router.register(r"user_type", UserTypeViewSet, basename="user_type")
router.register(r"users", UserViewSet, basename="users")
router.register(r"currency-master", CurrencyMasterViewSet, basename="currency-master")


urlpatterns = [
    # Login apis
    path("auth/register/", RegistrationAPIView.as_view(), name="user_register"),
    path("auth/login/", LoginAPIView.as_view(), name="user_login"),
    path("auth/logout/", LogoutView.as_view(), name="auth_logout"),
    # For OTP
    path("auth/otp_generate/", OTPGenerateAPIView.as_view(), name="otp_generate"),
    path(
        "auth/otp_verification/",
        OTPVerificationAPIView.as_view(),
        name="otp_verification",
    ),
    # Token apis
    # path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # dj rest auth
    path("auth/password/reset/", PasswordResetView.as_view(), name="password_reset"),
    # path(
    #     "auth/password/reset/confirm/<uidb64>/<token>/",
    #     PasswordResetConfirmView.as_view(),
    #     name="password_reset_confirm",
    # ),
    path(
        "auth/password/reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "auth/password/change/",
        PasswordChangeView.as_view(),
        name="rest_password_change",
    ),
    path("auth/google/", GoogleLogin.as_view(), name="google_login"),
    path("auth/google/refresh", google_token, name="google_refresh_login"),
    path("auth/apple/", AppleLogin.as_view(), name="apple_login"),
    # Notification send apis
    path("send_email/", EmailSendView.as_view(), name="email_send"),
    path("whats_app/", WhatsAPPView.as_view(), name="whats_app_message"),
]

urlpatterns += router.urls
