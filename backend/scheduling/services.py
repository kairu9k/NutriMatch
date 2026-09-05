"""Daily.co video consultation session service.

Security notes:
 - API key is read from settings.DAILY_CO only — never hardcoded.
 - host_url is stored on ConsultationSession but must never be exposed to
   client-facing API responses (RND-only — grants host/owner controls).
 - participant_url is the only URL that may be returned to clients.
"""

import secrets
import string
from datetime import timedelta

import httpx
from django.conf import settings


class VideoSessionError(Exception):
    pass


def _random_suffix(length=8):
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


class DailyCoVideoService:
    def __init__(self):
        cfg = settings.DAILY_CO
        self.api_key = cfg["API_KEY"]
        self.base_url = cfg["BASE_URL"]
        self.timeout = cfg["TIMEOUT"]

    def _client(self):
        if not self.api_key:
            raise VideoSessionError("DAILY_CO_API_KEY is not configured.")
        return httpx.Client(headers={"Authorization": f"Bearer {self.api_key}"}, timeout=self.timeout)

    def create_room(self, appointment) -> dict:
        """Create a Daily.co room for the appointment. Room expires
        automatically after the scheduled duration.

        Returns {'external_session_id', 'host_url', 'participant_url'}.
        """
        room_name = f"nm-appt-{appointment.id}-{_random_suffix()}"
        duration = appointment.duration_minutes or 60
        expires_at = appointment.scheduled_at + timedelta(minutes=duration)

        with self._client() as client:
            response = client.post(
                f"{self.base_url}/rooms",
                json={
                    "name": room_name,
                    "properties": {
                        "exp": int(expires_at.timestamp()),
                        "enable_chat": True,
                        "start_video_off": False,
                    },
                },
            )

        if response.is_error:
            raise VideoSessionError("Video session could not be created. Please try again.")

        room = response.json()

        return {
            "external_session_id": room_name,
            "host_url": f"{room['url']}?t={self._generate_host_token(room_name)}",
            "participant_url": room["url"],
        }

    def delete_room(self, external_session_id: str) -> bool:
        with self._client() as client:
            response = client.delete(f"{self.base_url}/rooms/{external_session_id}")
        return not response.is_error

    def _generate_host_token(self, room_name: str) -> str:
        with self._client() as client:
            response = client.post(
                f"{self.base_url}/meeting-tokens",
                json={"properties": {"room_name": room_name, "is_owner": True}},
            )
        if response.is_error:
            return ""
        return response.json().get("token", "")
