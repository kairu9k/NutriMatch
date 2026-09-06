from django.urls import path

from .views import (
    MyClientProfileView,
    MyRndProfileView,
    RndAvailabilityDetailView,
    RndAvailabilityListCreateView,
    RndClientProfileView,
    RndDetailView,
    RndPublicAvailabilityView,
    RndPublicReviewsView,
    RndSearchView,
)

urlpatterns = [
    path("client/rnds/", RndSearchView.as_view(), name="rnd_search"),
    path("client/rnds/<int:rnd_id>/", RndDetailView.as_view(), name="rnd_detail"),
    path("client/rnds/<int:rnd_id>/reviews/", RndPublicReviewsView.as_view(), name="rnd_public_reviews"),
    path("client/rnds/<int:rnd_id>/availability/", RndPublicAvailabilityView.as_view(), name="rnd_public_availability"),
    path("rnd/profile/", MyRndProfileView.as_view(), name="my_rnd_profile"),
    path("rnd/availability/", RndAvailabilityListCreateView.as_view(), name="rnd_availability"),
    path("rnd/availability/<int:pk>/", RndAvailabilityDetailView.as_view(), name="rnd_availability_detail"),
    path("client/profile/", MyClientProfileView.as_view(), name="my_client_profile"),
    path("rnd/relationships/<int:relationship_id>/client-profile/", RndClientProfileView.as_view(), name="rnd_client_profile"),
]
