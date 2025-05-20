import datetime

from django.utils.deprecation import MiddlewareMixin

from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError


class JWTAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        access_token = request.COOKIES.get('access_token')
        refresh_token = request.COOKIES.get('refresh_token')

        if access_token:
            try:
                token = AccessToken(access_token)

                if datetime.datetime.fromtimestamp(
                    token['exp'], datetime.UTC
                ) < datetime.datetime.now(tz=datetime.UTC):
                    raise TokenError('Token expired')

                request.META['HTTP_AUTHORIZATION'] = f"Bearer {access_token}"
            except TokenError:
                new_access_token = self.refresh_access_token(refresh_token)

                if new_access_token:
                    request.META['HTTP_AUTHORIZATION'] = f"Bearer {new_access_token}"

                    request._new_access_token = new_access_token
                else:
                    self.clear_cookies(request)

        elif refresh_token:
            new_access_token = self.refresh_access_token(refresh_token)

            if new_access_token:
                request.META['HTTP_AUTHORIZATION'] = f"Bearer {new_access_token}"
                request._new_access_token = new_access_token
            else:
                self.clear_cookies(request)

    def process_response(self, request, response):
        new_access = getattr(request, '_new_access_token', None)

        if new_access:
            access_exp = AccessToken(new_access)['exp']

            response.set_cookies(
                key='access_token',
                value=new_access,
                httponly=True,
                secure=False,
                samesite='Lax',
                expires=datetime.datetime.fromtimestamp(access_exp, datetime.UTC)
            )

        return response

    def refresh_access_token(self, refresh_token):
        try:
            refresh = RefreshToken(refresh_token)

            new_access_token = str(refresh.access_token)

            return new_access_token

        except TokenError:
            return None

    def clear_cookies(self, request):
        request.COOKIES.pop('access_token')
        request.COOKIES.pop('refresh_token')