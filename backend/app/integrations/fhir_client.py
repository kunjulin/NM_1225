from __future__ import annotations

import json
from typing import Any
from urllib import request
from uuid import uuid4

from app.settings import get_settings


def create_medication_request(payload: dict[str, Any]) -> str:
    settings = get_settings()
    base_url = (getattr(settings, "fhir_base_url", None) or "").strip()
    if settings.app_mode == "demo" or not base_url:
        resource_id = f"MedicationRequest/demo-{uuid4()}"
        print(f"[demo] MedicationRequest created: {resource_id}")
        print(json.dumps(payload, indent=2))
        return resource_id

    url = base_url.rstrip("/") + "/MedicationRequest"
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/fhir+json"},
        method="POST",
    )
    with request.urlopen(req, timeout=10) as response:
        raw = response.read().decode("utf-8")
        response_payload = json.loads(raw) if raw else {}
        location = response.headers.get("Location")
    resource_id = response_payload.get("id") or response_payload.get("resource", {}).get("id")
    if not resource_id and location:
        resource_id = location.rsplit("/", 1)[-1]
    if not resource_id:
        resource_id = f"MedicationRequest/{uuid4()}"
    return f"MedicationRequest/{resource_id}"
