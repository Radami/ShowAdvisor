from django.contrib import admin
from django.urls import include, path

from accounts.views import GoogleLoginView, ProfileView
from dj_rest_auth.jwt_auth import get_refresh_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/google/", GoogleLoginView.as_view(), name="google_login"),
    path("api/auth/token/refresh/", get_refresh_view().as_view(), name="token_refresh"),
    path("api/profile/", ProfileView.as_view(), name="profile"),
    path("api/", include("catalog.urls")),
    path("api/", include("tracking.urls")),
]
