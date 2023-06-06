from typing import Type

from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.apple.views import (
    AppleOAuth2Adapter,
    AppleOAuth2Client,
)
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.conf import settings
from django.db.models import Model, ProtectedError
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, status, views, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from foundation.api.exceptions import (
    ExpiredOtpException,
    InvalidOtpException,
    ProtectedErrorException,
)
from foundation.api.serializers import (
    CurrencyMasterSerializer,
    CustomSocialLoginSerializer,
    EmailSendSerializer,
    LoginSerializer,
    LogoutSerializer,
    OTPGenerateSerializer,
    OtpVerifySerializer,
    PasswordResetSerializer,
    RegistrationSerializer,
    UserSerializer,
    UserTypeSerializer,
    WhatsAPPSerializer,
    get_tokens_for_user,
    get_user_information,
)
from foundation.models import CurrencyMaster, User, UserAuthenticationOption, UserType


class RegistrationAPIView(generics.GenericAPIView):
    """
    Register new users usingemail and password.
    """

    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "user": get_user_information(user),
                "token": get_tokens_for_user(user),
            },
            status=status.HTTP_200_OK,
        )


class LoginAPIView(generics.GenericAPIView):
    """
    Getting otp existing users using email and password if the two_step_verification is enabled.
    Or,
    Getting token using email and password.
    """

    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = request.data.get("email")
        user = User.objects.get(email=email, is_active=True)

        try:
            user_authentication = UserAuthenticationOption.objects.get(user=user)

            if user_authentication.two_step_verification:
                return Response(
                    {
                        "two_step_verification": user_authentication.two_step_verification,
                        "device_authenticator": user_authentication.device_authenticator,
                        "otp_verification": user_authentication.otp_verification,
                    },
                    status=status.HTTP_200_OK,
                )
        except UserAuthenticationOption.DoesNotExist:
            pass

        context = {"user": get_user_information(user)}
        context.update(get_tokens_for_user(user))

        return Response(context, status=status.HTTP_200_OK)


class OTPGenerateAPIView(generics.GenericAPIView):
    """
    Getting otp existing users using username or email and password.
    """

    serializer_class = OTPGenerateSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        otp_method = request.data.get("otp_method")

        return Response(
            {"send": f"OTP successfully send to the {otp_method}!!!"},
            status=status.HTTP_200_OK,
        )


class OTPVerificationAPIView(generics.GenericAPIView):
    """
    Authenticate existing users using otp.
    """

    serializer_class = OtpVerifySerializer
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            otp = request.data.get("otp")
            user_auth = UserAuthenticationOption.objects.get(
                otp=otp, user__is_active=True
            )
            now = timezone.now()

            if user_auth.otp_expired_at > now:
                user_auth.otp = None
                user_auth.user.last_login = now
                user_auth.save()

                user = user_auth.user

                context = {"user": get_user_information(user)}
                context.update(get_tokens_for_user(user))

                return Response(context, status=status.HTTP_200_OK)
            else:
                raise ExpiredOtpException()

        except UserAuthenticationOption.DoesNotExist:
            raise InvalidOtpException()


class LogoutView(views.APIView):
    """
    Logout an authenticated user.
    """

    serializer_class = LogoutSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"details": "Successful Logout"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"details": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CustomSocialLoginView(SocialLoginView):
    """
    Coustomize the SocialLoginview
    """

    serializer_class = CustomSocialLoginSerializer


class GoogleLogin(CustomSocialLoginView):
    authentication_classes = []  # disable  authentication
    adapter_class = GoogleOAuth2Adapter
    callback_url = settings.CALLBACK_URL
    client_class = OAuth2Client

    def get_response(self):
        serializer_class = self.get_response_serializer()
        user = self.request.user

        # Get user type and insert into User model
        user.user_type_id = self.request._data.get("user_type")
        user.save()

        serializer = serializer_class(
            instance=self.token, context={"request": self.request}
        )
        resp = serializer.data
        response = Response(resp, status=status.HTTP_200_OK)

        return response


@csrf_exempt
def google_token(request):
    if "code" not in request.body.decode():
        from rest_framework_simplejwt.settings import api_settings as jwt_settings
        from rest_framework_simplejwt.views import TokenRefreshView

        class RefreshNuxtAuth(TokenRefreshView):
            # By default, Nuxt auth accept and expect postfix "_token"
            # while simple_jwt library doesnt accept nor expect that postfix
            def post(self, request, *args, **kwargs):
                request.data._mutable = True
                request.data["refresh"] = request.data.get("refresh_token")
                request.data._mutable = False
                response = super().post(request, *args, **kwargs)
                response.data["refresh_token"] = response.data["refresh"]
                response.data["access_token"] = response.data["access"]
                return response

        return RefreshNuxtAuth.as_view()(request)

    else:
        return GoogleLogin.as_view()(request)


class AppleLogin(SocialLoginView):
    adapter_class = AppleOAuth2Adapter
    callback_url = settings.CALLBACK_URL
    client_class = AppleOAuth2Client


class PasswordResetView(generics.GenericAPIView):
    """
    Calls PasswordResetSerailizer save method.

    Accepts the following POST parameters: email
    Returns the success/fail message.
    """

    serializer_class = PasswordResetSerializer
    permission_classes = [
        AllowAny,
    ]

    def post(self, request, *args, **kwargs):
        # Create a serializer with request.data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(request)
        # Return the success message with OK HTTP status
        return Response(
            {"detail": _("Password reset e-mail has been sent.")},
            status=status.HTTP_200_OK,
        )


class BaseModelViewSet(viewsets.ModelViewSet):
    """
    A viewset for generic model viewset.
    """

    permission_classes = (IsAuthenticated,)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
            return Response(
                {"details": "Deleted successfully."}, status=status.HTTP_204_NO_CONTENT
            )

        # if protected, cannot be deleted, show error message
        except ProtectedError as exception:
            raise ProtectedErrorException


class MasterGenericViewSet(BaseModelViewSet):
    """
    A generic viewset for viewing and editing master instances.
    """

    model: Type[Model]

    def get_queryset(self):
        return self.model.objects.all()


class EmailSendView(generics.GenericAPIView):
    """
    Calls EmailSendSerializer save method.

    Accepts the following POST parameters: email, subject, message
    Returns the success/fail message.
    """

    parser_classes = (MultiPartParser, FormParser)
    serializer_class = EmailSendSerializer
    permission_classes = [
        AllowAny,
    ]

    def post(self, request, *args, **kwargs):
        # Create a serializer with request.data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(request)

        # Return the success message with OK HTTP status
        return Response(
            {"detail": _("E-mail has been sent.")},
            status=status.HTTP_200_OK,
        )


class WhatsAPPView(generics.GenericAPIView):
    """
    Calls WhatsAPPSerializer save method.

    Accepts the following POST parameters: phone number, message
    Returns the success/fail message.
    """

    serializer_class = WhatsAPPSerializer
    permission_classes = [
        AllowAny,
    ]

    def post(self, request, *args, **kwargs):
        # Create a serializer with request.data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(request)
        # Return the success message with OK HTTP status
        return Response(
            {"detail": _("Whats app message has been sent.")},
            status=status.HTTP_200_OK,
        )


class UserTypeViewSet(MasterGenericViewSet):
    """
    A viewset for viewingUserType instances.
    """

    model = UserType
    serializer_class = UserTypeSerializer
    permission_classes = (AllowAny,)
    http_method_names = ("get",)


class UserViewSet(MasterGenericViewSet):
    """
    A viewset for viewing Users instances.
    """

    model = User
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ("get",)


class CurrencyMasterViewSet(MasterGenericViewSet):
    """
    A simple ViewSet for viewing Currency Master.
    """

    model = CurrencyMaster
    serializer_class = CurrencyMasterSerializer
    http_method_names = ("get",)
