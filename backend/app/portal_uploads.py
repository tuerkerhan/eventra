import os
import shutil
from typing import Any


UPLOAD_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
PORTAL_UPLOAD_ROOT = os.path.join(UPLOAD_ROOT, "portal")


def portal_event_dir(salon_id: str, event_id: str) -> str:
    return os.path.join(PORTAL_UPLOAD_ROOT, salon_id, event_id)


def portal_salon_dir(salon_id: str) -> str:
    return os.path.join(PORTAL_UPLOAD_ROOT, salon_id)


def delete_portal_event_uploads(salon_id: str, event_id: str) -> None:
    shutil.rmtree(portal_event_dir(salon_id, event_id), ignore_errors=True)


def delete_portal_salon_uploads(salon_id: str) -> None:
    shutil.rmtree(portal_salon_dir(salon_id), ignore_errors=True)


def _portal_url_to_path(url: str) -> str | None:
    prefix = "/uploads/portal/"
    if not url.startswith(prefix):
        return None
    rel = url[len("/uploads/"):]
    path = os.path.abspath(os.path.join(UPLOAD_ROOT, rel))
    if not path.startswith(os.path.abspath(PORTAL_UPLOAD_ROOT) + os.sep):
        return None
    return path


def delete_submission_photos(data: dict[str, Any] | None) -> None:
    photos = (data or {}).get("__photos")
    if not isinstance(photos, list):
        return
    for photo in photos:
        if not isinstance(photo, dict):
            continue
        url = photo.get("url")
        if not isinstance(url, str):
            continue
        path = _portal_url_to_path(url)
        if path and os.path.isfile(path):
            os.remove(path)
