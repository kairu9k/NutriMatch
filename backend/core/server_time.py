"""Every response says the server's current time (X-Server-Time, epoch ms).
The frontend follows this clock instead of the device's
(frontend/app/plugins/00.ph-time.client.ts), so changing a phone's date or
time changes nothing. Exposed to the browser via CORS_EXPOSE_HEADERS."""

import time


def server_time_middleware(get_response):
    def middleware(request):
        response = get_response(request)
        response["X-Server-Time"] = str(int(time.time() * 1000))
        return response

    return middleware
