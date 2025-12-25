from __future__ import annotations

import csv
import io
import json
import zipfile
from datetime import datetime, timezone
from typing import Any

from app.services.analytics import autofill_summary, summary
from app.settings import get_settings


def _csv_bytes(rows: list[dict[str, Any]], fieldnames: list[str]) -> bytes:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue().encode("utf-8")


def export_summary_csv(db, from_date: str, to_date: str) -> bytes:
    data = summary(db, from_date, to_date)
    counts = data.get("counts", {})
    kpis = data.get("kpis", {})
    tat = data.get("tat", {})

    row = {
        "from": from_date,
        "to": to_date,
        "totalCasesCreated": counts.get("totalCasesCreated"),
        "submittedToPharmacy": counts.get("submittedToPharmacy"),
        "approvals": counts.get("approvals"),
        "pharmacistInterventions": counts.get("pharmacistInterventions"),
        "pharmacistInterventionRate": kpis.get("pharmacistInterventionRate"),
        "inappropriateDoseCases": kpis.get("inappropriateDoseCases"),
        "inappropriateDoseRate": kpis.get("inappropriateDoseRate"),
        "syncDone": counts.get("syncDone"),
        "syncFailed": counts.get("syncFailed"),
        "tat_submit_to_first_pharm_action_p50_seconds": (
            tat.get("submitToFirstPharmAction", {}).get("p50Seconds")
        ),
        "tat_submit_to_first_pharm_action_p90_seconds": (
            tat.get("submitToFirstPharmAction", {}).get("p90Seconds")
        ),
        "tat_submit_to_decision_p50_seconds": tat.get("submitToDecision", {}).get(
            "p50Seconds"
        ),
        "tat_submit_to_decision_p90_seconds": tat.get("submitToDecision", {}).get(
            "p90Seconds"
        ),
        "tat_approve_to_sync_done_p50_seconds": tat.get("approveToSyncDone", {}).get(
            "p50Seconds"
        ),
        "tat_approve_to_sync_done_p90_seconds": tat.get("approveToSyncDone", {}).get(
            "p90Seconds"
        ),
    }
    fieldnames = list(row.keys())
    return _csv_bytes([row], fieldnames)


def export_returns_csv(db, from_date: str, to_date: str) -> bytes:
    data = summary(db, from_date, to_date)
    distributions = data.get("distributions", {})
    return_reasons = distributions.get("returnReasons", []) or []
    total_returns = data.get("counts", {}).get("pharmacistInterventions", 0) or 0

    rows = []
    for entry in return_reasons:
        count = entry.get("count", 0) or 0
        proportion = count / total_returns if total_returns else 0.0
        rows.append(
            {
                "from": from_date,
                "to": to_date,
                "reasonCode": entry.get("code"),
                "count": count,
                "proportion": proportion,
            }
        )

    fieldnames = ["from", "to", "reasonCode", "count", "proportion"]
    return _csv_bytes(rows, fieldnames)


def export_tat_csv(db, from_date: str, to_date: str) -> bytes:
    data = summary(db, from_date, to_date)
    tat = data.get("tat", {})

    mapping = {
        "submit_to_first_pharm_action": tat.get("submitToFirstPharmAction", {}),
        "submit_to_decision": tat.get("submitToDecision", {}),
        "approve_to_sync_done": tat.get("approveToSyncDone", {}),
    }

    rows = []
    for metric, values in mapping.items():
        rows.append(
            {
                "from": from_date,
                "to": to_date,
                "tatMetric": metric,
                "count": values.get("count"),
                "p50Seconds": values.get("p50Seconds"),
                "p90Seconds": values.get("p90Seconds"),
                "meanSeconds": values.get("meanSeconds"),
            }
        )

    fieldnames = ["from", "to", "tatMetric", "count", "p50Seconds", "p90Seconds", "meanSeconds"]
    return _csv_bytes(rows, fieldnames)


def export_autofill_csv(db, from_date: str, to_date: str) -> bytes:
    data = autofill_summary(db, from_date, to_date)
    autofill = data.get("autofill", {})
    by_fact = autofill.get("byFactType", []) or []
    impact = autofill.get("impact", {})

    rows = []
    total_accepted = 0
    total_rejected = 0
    total_missing_resolved = 0

    for entry in by_fact:
        fact_type = entry.get("factType")
        accepted = entry.get("accepted", 0) or 0
        rejected = entry.get("rejected", 0) or 0
        total = accepted + rejected
        accept_rate = accepted / total if total else 0.0

        missing_resolved = ""
        if fact_type == "WEIGHT_KG":
            missing_resolved = impact.get("missingWeightResolved", "")
        elif fact_type in {"EGFR", "SCR_MGDL"}:
            missing_resolved = impact.get("missingRenalResolved", "")

        rows.append(
            {
                "from": from_date,
                "to": to_date,
                "factType": fact_type,
                "accepted": accepted,
                "rejected": rejected,
                "acceptRate": accept_rate,
                "missingResolved": missing_resolved,
            }
        )
        total_accepted += accepted
        total_rejected += rejected
        if isinstance(missing_resolved, int):
            total_missing_resolved += missing_resolved

    total = total_accepted + total_rejected
    total_accept_rate = total_accepted / total if total else 0.0
    rows.append(
        {
            "from": from_date,
            "to": to_date,
            "factType": "__TOTAL__",
            "accepted": total_accepted,
            "rejected": total_rejected,
            "acceptRate": total_accept_rate,
            "missingResolved": total_missing_resolved or "",
        }
    )

    fieldnames = ["from", "to", "factType", "accepted", "rejected", "acceptRate", "missingResolved"]
    return _csv_bytes(rows, fieldnames)


def export_all_zip(db, from_date: str, to_date: str) -> bytes:
    summary_csv = export_summary_csv(db, from_date, to_date)
    returns_csv = export_returns_csv(db, from_date, to_date)
    tat_csv = export_tat_csv(db, from_date, to_date)
    autofill_csv = export_autofill_csv(db, from_date, to_date)

    settings = get_settings()
    metadata = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "from": from_date,
        "to": to_date,
        "appMode": settings.app_mode,
    }

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("summary.csv", summary_csv)
        archive.writestr("returns.csv", returns_csv)
        archive.writestr("tat.csv", tat_csv)
        archive.writestr("autofill.csv", autofill_csv)
        archive.writestr("metadata.json", json.dumps(metadata, indent=2))
    buffer.seek(0)
    return buffer.getvalue()
