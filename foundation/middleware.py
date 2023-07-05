from .utils.base import _thread_locals, set_current_user


class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        set_current_user(getattr(request, "user", None))

        response = self.get_response(request)

        self.remove_current_user()
        # Code to be executed for each request/response after
        # the view is called.

        return response

    def remove_current_user(self):
        _thread_locals.user = None
