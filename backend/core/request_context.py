"""The request being handled, so audit rows can record where an action came
from without every caller passing the request along (2026-10-26: payouts,
refunds, approvals and password changes were saved with no IP at all).

`client_ip()` reads X-Forwarded-For first: on Render the app sits behind a
proxy, so REMOTE_ADDR is the proxy, not the person. The header's first entry
is the original client. A client can put its own value in front of it, so the
IP is a lead for an investigation, not proof (same as any app behind a proxy).
"""

from contextvars import ContextVar

_current_request = ContextVar("current_request", default=None)


def current_request():
    return _current_request.get()


def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        first = forwarded.split(",")[0].strip()
        if first:
            return first[:45]
    return (request.META.get("REMOTE_ADDR") or "")[:45] or None


def current_request_middleware(get_response):
    def middleware(request):
        token = _current_request.set(request)
        try:
            return get_response(request)
        finally:
            _current_request.reset(token)

    return middleware
