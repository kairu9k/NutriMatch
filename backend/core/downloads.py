"""Fetching private Cloudinary files server-side, fast.

Cloudinary's API download link (`private_download_url`) trickles from here (a
5 MB PDF took well over 30 s, a 145 KB photo 16 s, 2026-10-24), while a signed
authenticated delivery URL on the CDN sends the same file in about a second.
So: CDN first, the API link only as a fallback, and an overall deadline on
each try so a slow download ends in an error instead of a spinner. The URLs
are only ever used on the server; the browser never sees them.
"""
import time

import httpx


def download(url, deadline=25):
    """GET the whole body within `deadline` seconds in total."""
    end = time.monotonic() + deadline
    chunks = []
    with httpx.stream("GET", url, timeout=10, follow_redirects=True) as resp:
        resp.raise_for_status()
        for chunk in resp.iter_bytes():
            chunks.append(chunk)
            if time.monotonic() > end:
                raise TimeoutError("download too slow")
    return b"".join(chunks)


def fetch_private_image(public_id, fmt, api_expires_at):
    """Bytes of an authenticated Cloudinary asset (resource_type image), or
    None when neither the CDN nor the API link delivers in time."""
    import cloudinary.utils

    cdn_url, _ = cloudinary.utils.cloudinary_url(
        public_id, resource_type="image", type="authenticated", sign_url=True, format=fmt, secure=True,
    )
    api_url = cloudinary.utils.private_download_url(
        public_id, fmt, resource_type="image", type="authenticated", expires_at=api_expires_at,
    )
    for url in (cdn_url, api_url):
        try:
            return download(url)
        except (httpx.HTTPError, TimeoutError):
            continue
    return None
