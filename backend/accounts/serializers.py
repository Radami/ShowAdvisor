from allauth.socialaccount.providers.oauth2.client import OAuth2Error
from dj_rest_auth.registration.serializers import SocialLoginSerializer
from rest_framework import serializers


class GoogleIdTokenLoginSerializer(SocialLoginSerializer):
    """
    The stock serializer rejects a bare {"id_token": ...} payload — its
    validate() demands access_token or code before doing anything else. But
    for Google it ultimately hands the id_token to allauth's adapter, which
    verifies it cryptographically and ignores the access token entirely, so
    an id_token alone is a complete credential. Mirror it into access_token
    to get past the stock validation.
    """

    def validate(self, attrs):
        if attrs.get("id_token") and not attrs.get("access_token"):
            attrs["access_token"] = attrs["id_token"]
        try:
            return super().validate(attrs)
        except OAuth2Error as ex:
            # Raised by allauth when the id_token is invalid/expired; the
            # parent only catches HTTPError, so this would otherwise be a 500.
            raise serializers.ValidationError("Invalid or expired Google id_token") from ex
