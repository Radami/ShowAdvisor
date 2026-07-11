from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import GoogleIdTokenLoginSerializer


class GoogleLoginView(SocialLoginView):
    """
    Exchanges a Google ID token (obtained natively by the mobile app) for
    this app's own JWT access/refresh pair (spec §5 Auth).

    POST {"id_token": "<google id token>"} -> {"access": ..., "refresh": ..., "user": ...}
    """

    adapter_class = GoogleOAuth2Adapter
    serializer_class = GoogleIdTokenLoginSerializer


class ProfileView(APIView):
    """Milestone 0.3 — the simplest possible authenticated endpoint."""

    def get(self, request):
        return Response(
            {
                "username": request.user.username,
                "email": request.user.email,
            }
        )
