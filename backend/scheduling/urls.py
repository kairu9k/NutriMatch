from django.urls import path

from .admin_views import AdminAppointmentCancelView, AdminAppointmentListView, AdminAppointmentSummaryView

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
    RndPatientListView,
    RndReviewListView,
)

urlpatterns = [
    path("client/relationships/", ClientActiveRelationshipsView.as_view(), name="client_active_relationships"),
    path("rnd/relationships/active/", RndActiveRelationshipsView.as_view(), name="rnd_active_relationships"),
    path("rnd/patients/", RndPatientListView.as_view(), name="rnd_patient_list"),

    path("client/appointments/", ClientAppointmentListCreateView.as_view(), name="client_appointments"),
    path("client/rnds/<int:rnd_id>/booked-slots/", RndBookedSlotsView.as_view(), name="rnd_booked_slots"),
    path("client/appointments/<int:pk>/", ClientAppointmentDetailView.as_view(), name="client_appointment_detail"),
    path("client/appointments/<int:pk>/cancel/", ClientAppointmentCancelView.as_view(), name="client_appointment_cancel"),

    path("rnd/appointments/", RndAppointmentListView.as_view(), name="rnd_appointments"),
    path("rnd/appointments/<int:pk>/", RndAppointmentDetailView.as_view(), name="rnd_appointment_detail"),
    path("rnd/appointments/<int:pk>/confirm/", RndAppointmentConfirmView.as_view(), name="rnd_appointment_confirm"),
    path("rnd/appointments/<int:pk>/complete/", RndAppointmentCompleteView.as_view(), name="rnd_appointment_complete"),
    path("rnd/appointments/<int:pk>/cancel/", RndAppointmentCancelView.as_view(), name="rnd_appointment_cancel"),

    path("client/reviews/", ClientReviewListCreateView.as_view(), name="client_reviews"),
    path("rnd/reviews/", RndReviewListView.as_view(), name="rnd_reviews"),

    path("admin/appointments/", AdminAppointmentListView.as_view(), name="admin_appointments"),
    path("admin/appointments/summary/", AdminAppointmentSummaryView.as_view(), name="admin_appointment_summary"),
    path("admin/appointments/<int:pk>/cancel/", AdminAppointmentCancelView.as_view(), name="admin_appointment_cancel"),
]
