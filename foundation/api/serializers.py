from typing import Dict

import django.contrib.auth.password_validation as validators
from allauth.account.utils import user_pk_to_url_str
from allauth.utils import build_absolute_uri
from constance import config
from dj_rest_auth.models import TokenModel
from dj_rest_auth.registration.serializers import SocialLoginSerializer
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import exceptions
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken


from drf_writable_nested.serializers import WritableNestedModelSerializer

from foundation.api.exceptions import (
    AccountDisabledException,
    ExistEmailrException,
    InactiveAccountException,
    InvalidCredentialsException,
    RequiredException,
    SendingOTPException,
)
from foundation.models import (
    CurrencyMaster,
    User,
    UserAuthenticationOption,
    UserInfo,
    UserType,
    Menu,
    MenuAction,
    UserMenuSecurity,
    UserTypeMenuPermission,
    UsersMenuPermission,
)
from foundation.utils.emails import send_email
from foundation.utils.notifications import (
    generate_otp,
    send_whatsapp_notification,
    welcome_email_notification,
)


def get_user_information(user: User) -> Dict:
    """Return user related information"""

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "user_type": user.user_type.id if user.user_type else None,
    }


def get_tokens_for_user(user: User) -> Dict:
    """Token generate"""

    refresh_token = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh_token),
        "access": str(refresh_token.access_token),
    }


class CustomTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = TokenModel
        fields = (
            "key",
            "user",
        )

    def to_representation(self, instance):
        res = super().to_representation(instance)
        user = instance.user

        res.update(
            {
                "user": get_user_information(user),
                "token": get_tokens_for_user(user),
            }
        )

        return res


class RegistrationSerializer(serializers.Serializer):
    """
    Serializer for register a new user.
    """

    name = serializers.CharField(max_length=30)
    email = serializers.EmailField()
    phone_number = PhoneNumberField(required=False, allow_blank=True)
    user_type = serializers.PrimaryKeyRelatedField(
        queryset=UserType.objects.all(),
        required=settings.SIGN_UP_USER_TYPE_REQUIRED,
        allow_null=settings.SIGN_UP_USER_TYPE_ALLOW_NULL,
    )  # Make allow_null=True or False, depend on user_type is needed or not
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    two_step_verification = serializers.BooleanField(default=False)
    device_authenticator = serializers.BooleanField(default=False)
    otp_verification = serializers.BooleanField(default=False)

    def _validate_email(self, email):
        # Unique validation
        user = User.objects.filter(email=email).exists()
        if user:
            raise ExistEmailrException()

        return email

    def _validate_password(self, user, password):
        errors = dict()
        try:
            # validate the password and catch the exception
            validators.validate_password(password=password, user=user)

        # the exception raised here is different than serializers.ValidationError
        except exceptions.ValidationError as e:
            errors["password"] = list(e.messages)

        if errors:
            raise serializers.ValidationError(errors)

        return password

    def _validate_two_step(self, data):
        two_step_verification = data.get("two_step_verification", None)
        device_authenticator = data.get("device_authenticator", None)
        otp_verification = data.get("otp_verification", None)

        if two_step_verification:
            if not device_authenticator and not otp_verification:
                raise serializers.ValidationError(
                    {"two_step_verification": "At least one step should be select."}
                )

        return data

    def validate(self, validated_data):
        email = validated_data.get("email", None)
        password = validated_data.get("password", None)

        if not email:
            raise RequiredException()

        if not password:
            raise RequiredException()

        # validate user email
        self._validate_email(email)

        # validate password
        user = User(email=validated_data["email"], password=validated_data["password"])
        self._validate_password(user, password)

        # validate two_step_verification
        self._validate_two_step(validated_data)

        return validated_data

    def create(self, validated_data):
        user = User.objects.create(
            name=validated_data["name"],
            email=validated_data["email"],
            user_type=validated_data["user_type"]
            if validated_data.get("user_type")
            else None,
        )
        user.set_password(validated_data["password"])
        user.save()

        if phone_number := validated_data.get("phone_number"):
            # Save data in UserInfo model
            UserInfo.objects.create(
                user=user,
                phone_number1=phone_number,
            )

        if two_step_verification := validated_data.get("two_step_verification"):
            # Save data in UserAuthenticationOption model
            UserAuthenticationOption.objects.create(
                user=user,
                two_step_verification=two_step_verification,
                device_authenticator=validated_data.get("device_authenticator"),
                otp_verification=validated_data.get("otp_verification"),
            )

        # Send welcome mail
        welcome_email_notification(user)

        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer to login users with email and password.
    """

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def _validate_user(self, email, password):
        user = None

        if email and password:
            user = authenticate(username=email, password=password)

        else:
            raise serializers.ValidationError(_("Enter an email and password."))

        return user

    def validate(self, validated_data):
        email = validated_data.get("email")
        password = validated_data.get("password")

        user = None

        user = self._validate_user(email, password)

        if not user:
            raise InvalidCredentialsException()

        if not user.is_active:
            raise AccountDisabledException()

        validated_data["user"] = user

        return validated_data


class CustomSocialLoginSerializer(SocialLoginSerializer):
    access_token = serializers.HiddenField(default=None)
    code = serializers.CharField(required=False, allow_blank=True)
    id_token = serializers.HiddenField(default=None)
    user_type = serializers.PrimaryKeyRelatedField(
        queryset=UserType.objects.all(),
        required=settings.SIGN_UP_USER_TYPE_REQUIRED,
        allow_null=settings.SIGN_UP_USER_TYPE_ALLOW_NULL,
    )  # Make allow_null=True or False, depend on user_type is needed or not

    def validate_code(self, value):
        if not value:
            raise serializers.ValidationError("Incorrect input. Code is required.")
        return value


class OTPGenerateSerializer(LoginSerializer):
    """
    Serializer to generate OTP.
    """

    OTP_METHOD_CHOICES = (
        ("email", "Email"),
        ("sms", "SMS"),
    )
    otp_method = serializers.ChoiceField(choices=OTP_METHOD_CHOICES)

    def validate(self, validated_data):
        email = validated_data.get("email")
        password = validated_data.get("password")
        otp_method = validated_data.get("otp_method")

        user = None

        user = self._validate_user(email, password)

        if not user:
            raise InvalidCredentialsException()

        if not user.is_active:
            raise AccountDisabledException()

        try:
            # Send OTP to the specific method
            generate_otp(user, otp_method)
        except ValueError as err:
            raise SendingOTPException()

        validated_data["user"] = user

        return validated_data


class OtpVerifySerializer(serializers.Serializer):
    """
    Serializer for verify otp
    """

    otp = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    """
    Serializer for logout
    """

    refresh_token = serializers.CharField()


class EmailAwarePasswordResetTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        ret = super(EmailAwarePasswordResetTokenGenerator, self)._make_hash_value(
            user, timestamp
        )
        email = user.email
        emails = set([email] if email else [])
        ret += "|".join(sorted(emails))
        return ret


default_token_generator = EmailAwarePasswordResetTokenGenerator()


class PasswordResetSerializer(serializers.Serializer):
    """
    Serializer for requesting a password reset e-mail.
    """

    email = serializers.EmailField()

    def _validate_email(self, email):
        user = None

        try:
            user = User.objects.get(email=email, is_active=True)
        except:
            raise InactiveAccountException

        return user

    def save(self, request, **kwargs):
        email = self.data["email"]

        user = self._validate_email(email)

        token_generator = kwargs.get("token_generator", default_token_generator)
        temp_key = token_generator.make_token(user)

        # send the password reset email
        # path = reverse(
        #     "foundation-api:password_reset_confirm",
        #     args=[user_pk_to_url_str(user), temp_key],
        # )
        # url = build_absolute_uri(request, path)

        # url = url.replace("%3F", "?")

        url = f"{settings.RESET_PASSWORD_LINK}/{user_pk_to_url_str(user)}/{temp_key}"

        context = {
            "site_name": config.SITE_NAME,
            "user": user,
            "password_reset_url": url,
            "request": request,
        }
        subject = "Password Reset E-mail"
        html_content = render_to_string(
            "foundation/emails/password_reset_key.html", context
        )

        send_email(
            subject,
            "A curated message for reset password.",
            html_content,
            mail_to=[email],
        )

        return self.data["email"]


class EmailSendSerializer(serializers.Serializer):
    """
    Serializer for requesting send e-mail.
    """

    to_email = serializers.EmailField()
    subject = serializers.CharField(max_length=100)
    message = serializers.CharField(max_length=255)
    # attachments = serializers.FileField(required=False)
    attachments = serializers.ListField(
        child=serializers.FileField(required=False), required=False
    )

    def save(self, request, **kwargs):
        to_email = request.data["to_email"]
        subject = request.data["subject"]
        message = request.data["message"]
        attachments = request.FILES.getlist("attachments")

        send_email(
            subject,
            "A curated message for sending notification.",
            message,
            mail_to=[to_email],
            attachments=attachments,
        )

        return self.data


class WhatsAPPSerializer(serializers.Serializer):
    """
    Serializer for requesting send whats app message.
    """

    phone_number = PhoneNumberField()
    message = serializers.CharField(max_length=255)

    def save(self, request, **kwargs):
        send_whatsapp_notification(
            self.data["phone_number"],
            self.data["message"],
        )

        return self.data


class UserTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserType
        fields = "__all__"


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ("password",)


class CurrencyMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrencyMaster
        fields = "__all__"


class MenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Menu
        fields = (
            "id",
            "name",
            "slug",
            "icon",
            "url",
            "order",
            "parent",
            "level",
            "visible_for_authenticated",
            "visible_for_anonymous",
        )


class MenuActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuAction
        fields = ("id", "action", "icon", "class_name")


class UserTypePermissionSerializer(serializers.ModelSerializer):
    menu = MenuSerializer()
    menu_action = MenuActionSerializer(many=True)

    class Meta:
        model = UserTypeMenuPermission
        fields = [
            "menu",
            "menu_action",
        ]
        depth = 1


class TypeMenuSecuritySerializer(serializers.ModelSerializer):
    menu = serializers.PrimaryKeyRelatedField(queryset=Menu.objects.all())

    class Meta:
        model = UserTypeMenuPermission
        fields = [
            "menu",
            "menu_action",
        ]


class TypeNestedMenuSecuritySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTypeMenuPermission
        exclude = ("user_type",)
        depth = 2


class UserTypeSecuritySerializer(WritableNestedModelSerializer):
    usertype_menu_set = TypeMenuSecuritySerializer(many=True)

    class Meta:
        model = UserType
        fields = (
            "id",
            "name",
            "visible_in_signup",
            "usertype_menu_set",
        )


class UserTypeNestedSecuritySerializer(serializers.ModelSerializer):
    usertype_menu_set = TypeNestedMenuSecuritySerializer(many=True)  # For depth

    class Meta:
        model = UserType
        fields = (
            "id",
            "name",
            "visible_in_signup",
            "usertype_menu_set",
        )


class UsersMenuPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsersMenuPermission
        exclude = ("users_menu",)


class UsersNestedMenuPermissionSerializer(UsersMenuPermissionSerializer):
    class Meta(UsersMenuPermissionSerializer.Meta):
        depth = 1


class UserSecuritySerializer(WritableNestedModelSerializer):
    users_menu_set = UsersMenuPermissionSerializer(many=True)

    class Meta:
        model = UserMenuSecurity
        fields = (
            "id",
            "users",
            "users_menu_set",
        )


class UserNestedSecuritySerializer(serializers.ModelSerializer):
    users_menu_set = UsersNestedMenuPermissionSerializer(many=True)  # For depth

    class Meta(UserSecuritySerializer.Meta):
        model = UserMenuSecurity
        fields = (
            "id",
            "users",
            "users_menu_set",
        )
        depth = 1


class UserPermissionSerializer(serializers.ModelSerializer):
    menu = MenuSerializer()
    menu_action = MenuActionSerializer(many=True)

    class Meta:
        model = UsersMenuPermission
        fields = [
            "menu",
            "menu_action",
        ]
        depth = 1
