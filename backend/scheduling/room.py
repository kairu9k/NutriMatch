"""Consultation room side panel for the client
(GET /api/client/appointments/<id>/room-info/): the RND's public details and
the client's own current meal-plan targets — nothing clinical the RND wrote
(no NCP drafts, notes or private progress notes), and never the video host link."""

from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsClient

from .models import Appointment


def _num(v):
    return float(v) if v is not None else None


def build_client_room_info(appointment):
    from nutrition.models import MealPlan

    rnd = appointment.relationship.rnd
    profile = getattr(rnd, "rnd_profile", None)
    plan = MealPlan.objects.filter(relationship=appointment.relationship, status=MealPlan.Status.ACTIVE).first()
    return {
        "rnd": {
            "name": rnd.full_name, "first_name": rnd.first_name, "profile_photo": rnd.profile_photo,
            "specialization": getattr(profile, "specialization", None),
        },
        "meal_plan": {
            "name": plan.name, "sent_at": plan.sent_at, "target_kcal": _num(plan.target_kcal),
            "target_carb_g": _num(plan.target_carb_g), "target_protein_g": _num(plan.target_protein_g),
            "target_fat_g": _num(plan.target_fat_g),
        } if plan else None,
    }


class ClientRoomInfoView(APIView):
    permission_classes = [IsClient]

    def get(self, request, pk):
        appointment = get_object_or_404(
            Appointment.objects.select_related("relationship__rnd__rnd_profile"),
            pk=pk, relationship__client=request.user,
        )
        return Response(build_client_room_info(appointment))
