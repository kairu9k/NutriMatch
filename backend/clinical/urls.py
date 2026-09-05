from django.urls import path

from .views import (
    NcpRecordDetailView,
    NcpRecordFinalizeView,
    NcpRecordListCreateView,
    ScreeningCreateView,
    ScreeningDetailView,
)

urlpatterns = [
    path("client/screening/", ScreeningCreateView.as_view(), name="screening_create"),
    path("client/screening/<int:appointment_id>/", ScreeningDetailView.as_view(), name="screening_detail"),

    path("rnd/relationships/<int:relationship_id>/ncp/", NcpRecordListCreateView.as_view(), name="ncp_list_create"),
    path("rnd/ncp/<int:pk>/", NcpRecordDetailView.as_view(), name="ncp_detail"),
    path("rnd/ncp/<int:pk>/finalize/", NcpRecordFinalizeView.as_view(), name="ncp_finalize"),
]
