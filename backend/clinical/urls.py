from django.urls import path

from .views import (
    ClientProgressRecordListView,
    LatestScreeningView,
    NcpRecordDetailView,
    NcpRecordFinalizeView,
    NcpRecordListCreateView,
    RndNcpDraftListView,
    RndProgressRecordListCreateView,
    ScreeningCreateView,
    ScreeningDetailView,
)

urlpatterns = [
    path("client/screening/", ScreeningCreateView.as_view(), name="screening_create"),
    path("client/screening/latest/", LatestScreeningView.as_view(), name="screening_latest"),
    path("client/screening/<int:appointment_id>/", ScreeningDetailView.as_view(), name="screening_detail"),

    path("rnd/relationships/<int:relationship_id>/ncp/", NcpRecordListCreateView.as_view(), name="ncp_list_create"),
    path("rnd/ncp/drafts/", RndNcpDraftListView.as_view(), name="rnd_ncp_drafts"),
    path("rnd/ncp/<int:pk>/", NcpRecordDetailView.as_view(), name="ncp_detail"),
    path("rnd/ncp/<int:pk>/finalize/", NcpRecordFinalizeView.as_view(), name="ncp_finalize"),

    path("rnd/relationships/<int:relationship_id>/progress/", RndProgressRecordListCreateView.as_view(), name="rnd_progress_list_create"),
    path("client/progress/", ClientProgressRecordListView.as_view(), name="client_progress_list"),
]
