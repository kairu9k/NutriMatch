from django.urls import path

from .labs import ClientLabFileView, ClientLabResultView, ClientLabsView, RndLabFileView, RndLabRequestCancelView, RndLabsView
from .ncp_context import NcpContextView
from .ncp_overview import NcpOverviewView
from .views import (
    ClientAdherenceView,
    ClientProgressRecordDetailView,
    ClientProgressRecordListView,
    LatestScreeningView,
    NcpRecordDetailView,
    NcpRecordFinalizeView,
    NcpRecordListCreateView,
    RndAppointmentScreeningView,
    RndNcpDraftListView,
    RndProgressRecordListCreateView,
    ScreeningCreateView,
    ScreeningDetailView,
)

urlpatterns = [
    path("client/screening/", ScreeningCreateView.as_view(), name="screening_create"),
    path("client/screening/latest/", LatestScreeningView.as_view(), name="screening_latest"),
    path("client/screening/<int:appointment_id>/", ScreeningDetailView.as_view(), name="screening_detail"),

    path("rnd/appointments/<int:appointment_id>/screening/", RndAppointmentScreeningView.as_view(), name="rnd_appointment_screening"),

    path("rnd/relationships/<int:relationship_id>/ncp/", NcpRecordListCreateView.as_view(), name="ncp_list_create"),
    path("rnd/relationships/<int:relationship_id>/ncp/context/", NcpContextView.as_view(), name="ncp_context"),
    path("rnd/ncp/drafts/", RndNcpDraftListView.as_view(), name="rnd_ncp_drafts"),
    path("rnd/ncp/overview/", NcpOverviewView.as_view(), name="rnd_ncp_overview"),
    path("rnd/ncp/<int:pk>/", NcpRecordDetailView.as_view(), name="ncp_detail"),
    path("rnd/ncp/<int:pk>/finalize/", NcpRecordFinalizeView.as_view(), name="ncp_finalize"),

    path("rnd/relationships/<int:relationship_id>/progress/", RndProgressRecordListCreateView.as_view(), name="rnd_progress_list_create"),
    path("client/progress/", ClientProgressRecordListView.as_view(), name="client_progress_list"),
    path("client/progress/<int:pk>/", ClientProgressRecordDetailView.as_view(), name="client_progress_detail"),
    path("client/adherence/", ClientAdherenceView.as_view(), name="client_adherence"),

    # lab results (clinical/labs.py)
    path("rnd/relationships/<int:relationship_id>/labs/", RndLabsView.as_view(), name="rnd_labs"),
    path("rnd/lab-requests/<int:pk>/", RndLabRequestCancelView.as_view(), name="rnd_lab_request_cancel"),
    path("rnd/lab-results/<int:pk>/file/", RndLabFileView.as_view(), name="rnd_lab_file"),
    path("client/labs/", ClientLabsView.as_view(), name="client_labs"),
    path("client/lab-results/<int:pk>/", ClientLabResultView.as_view(), name="client_lab_result"),
    path("client/lab-results/<int:pk>/file/", ClientLabFileView.as_view(), name="client_lab_file"),
]
