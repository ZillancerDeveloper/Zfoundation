from django.conf import settings

from .serializers import UserSerializer as DefaultUserSerializer

from .utils import import_callable

serializers = getattr(settings, "USER_INFO_SERIALIZERS", {})

UserSerializer = import_callable(
    serializers.get("USER_SERIALIZER", DefaultUserSerializer)
)
