from django.urls import path

from .views import (
    MyClientProfileView,
    MyRndProfileView,
    RndClientProfileView,
    RndDetailView,
    RndPublicReviewsView,
    RndSearchView,
)

urlpatterns = [
    path("client/rnds/", RndSearchView.as_view(), name="rnd_search"),
    path("client/rnds/<int:rnd_id>/", RndDetailView.as_view(), name="rnd_detail"),
    path("client/rnds/<int:rnd_id>/reviews/", RndPublicReviewsView.as_view(), name="rnd_public_reviews"),
    path("rnd/profile/", MyRndProfileView.as_view(), name="my_rnd_profile"),
    path("client/profile/", MyClientProfileView.as_view(), name="my_client_profile"),
    path("rnd/relationships/<int:relationship_id>/client-profile/", RndClientProfileView.as_view(), name="rnd_client_profile"),
]
