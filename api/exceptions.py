from django.utils.translation import gettext as _
from rest_framework.exceptions import APIException


class RequiredException(APIException):
    status_code = 400
    default_detail = _("Required fields are empty.")
    default_code = "required-field"


class ExistEmailrException(APIException):
    status_code = 400
    default_detail = _("This Email already exists. Please enter a new email.")
    default_code = "exist-email"


class InvalidCredentialsException(APIException):
    status_code = 401
    default_detail = _("Wrong email or password.")
    default_code = "invalid-credentials"


class AccountDisabledException(APIException):
    status_code = 403
    default_detail = _("User account is disabled.")
    default_code = "account-disabled"


class InactiveAccountException(APIException):
    status_code = 403
    default_detail = _("No active account with this email.")
    default_code = "account-inactive"


class ProtectedErrorException(APIException):
    status_code = 400
    default_detail = _("Cannot delete as it is related with others.")
    default_code = "server_error"


class SendingOTPException(APIException):
    status_code = 500
    default_detail = _("Something went wrong to send otp.")
    default_code = "send-otp-error"


class ExpiredOtpException(APIException):
    status_code = 408
    default_detail = _("Given otp is expired!!")
    default_code = "time-out"


class InvalidOtpException(APIException):
    status_code = 400
    default_detail = _("Invalid otp OR No any active user found for given otp")
    default_code = "invalid-otp"
