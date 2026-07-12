from django.urls import path

from .views import MovieDetailView, SearchView, ShowDetailView

urlpatterns = [
    path("search/", SearchView.as_view(), name="search"),
    path("shows/<int:pk>/", ShowDetailView.as_view(), name="show_detail"),
    path("movies/<int:pk>/", MovieDetailView.as_view(), name="movie_detail"),
]
