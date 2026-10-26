from django.urls import path

from .admin_views import AdminAppointmentCancelView, AdminAppointmentListView, AdminAppointmentSummaryView
from .discharge import RndDischargeView
from .discharge_requests import ClientDischargeRequestView
from .rnd_activity import RndActivityView
from .patient_list import RndPatientListView
from .patient_summary import RndPatientSummaryView
from .rnd_appointments import RndAppointmentBoardView
from .consultation_summary import ClientConsultationSummaryView, RndConsultationSummaryView
from .video_call import CallConfigView
from .room import ClientRoomInfoView
from .rnd_dashboard import RndDashboardView

from .views import (
    ClientActiveRelationshipsView,
    ClientAppointmentCancelView,
    ClientAppointmentDetailView,
    ClientAppointmentListCreateView,
    RndBookedSlotsView,
    ClientReviewListCreateView,
    RndActiveRelationshipsView,
    RndAppointmentCancelView,
    RndAppointmentCompleteView,
    RndAppointmentConfirmView,
    RndAppointmentDetailView,
    RndAppointmentListView,
    RndReviewListView,
)

urlpatterns = [
    path("client/relationships/", ClientActiveRelationshipsView.as_view(), name="client_active_relationships"),
    path("client/relationships/<int:pk>/discharge-request/", ClientDischargeRequestView.as_view(), name="client_discharge_request"),
    path("rnd/relationships/active/", RndActiveRelationshipsView.as_view(), name="rnd_active_relationships"),
    path("rnd/patients/", RndPatientListView.as_view(), name="rnd_patient_list"),
    path("rnd/relationships/<int:pk>/discharge/", RndDischargeView.as_view(), name="rnd_discharge"),
    path("rnd/relationships/<int:pk>/summary/", RndPatientSummaryView.as_view(), name="rnd_patient_summary"),

    path("client/appointments/", ClientAppointmentListCreateView.as_view(), name="client_appointments"),
    path("client/rnds/<int:rnd_id>/booked-slots/", RndBookedSlotsView.as_view(), name="rnd_booked_slots"),
    path("client/appointments/<int:pk>/", ClientAppointmentDetailView.as_view(), name="client_appointment_detail"),
    path("client/appointments/<int:pk>/cancel/", ClientAppointmentCancelView.as_view(), name="client_appointment_cancel"),
    path("client/appointments/<int:pk>/room-info/", ClientRoomInfoView.as_view(), name="client_room_info"),
    path("appointments/<int:pk>/call-config/", CallConfigView.as_view(), name="call_config"),
    path("client/appointments/<int:pk>/summary/", ClientConsultationSummaryView.as_view(), name="client_consultation_summary"),
    path("rnd/appointments/<int:pk>/summary/", RndConsultationSummaryView.as_view(), name="rnd_consultation_summary"),

    path("rnd/appointments/", RndAppointmentListView.as_view(), name="rnd_appointments"),
    path("rnd/appointments/board/", RndAppointmentBoardView.as_view(), name="rnd_appointment_board"),
    path("rnd/appointments/<int:pk>/", RndAppointmentDetailView.as_view(), name="rnd_appointment_detail"),
    path("rnd/appointments/<int:pk>/confirm/", RndAppointmentConfirmView.as_view(), name="rnd_appointment_confirm"),
    path("rnd/appointments/<int:pk>/complete/", RndAppointmentCompleteView.as_view(), name="rnd_appointment_complete"),
    path("rnd/appointments/<int:pk>/cancel/", RndAppointmentCancelView.as_view(), name="rnd_appointment_cancel"),

    path("client/reviews/", ClientReviewListCreateView.as_view(), name="client_reviews"),
    path("rnd/reviews/", RndReviewListView.as_view(), name="rnd_reviews"),
    path("rnd/activity/", RndActivityView.as_view(), name="rnd_activity"),

    path("rnd/dashboard/", RndDashboardView.as_view(), name="rnd_dashboard"),
    path("admin/appointments/", AdminAppointmentListView.as_view(), name="admin_appointments"),
    path("admin/appointments/summary/", AdminAppointmentSummaryView.as_view(), name="admin_appointment_summary"),
    path("admin/appointments/<int:pk>/cancel/", AdminAppointmentCancelView.as_view(), name="admin_appointment_cancel"),
]
