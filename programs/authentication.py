from django.contrib.auth.models import User
from rest_framework import authentication
from rest_framework import exceptions

class ParamKeyAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        key = request.GET.get('key', '')
        if not key:
            return None

        try:
            user = User.objects.get(auth_token=key)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('No such user')

        return (user, None)
