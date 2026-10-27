"""Pure, bounded reminder scheduling; no transport or storage effects."""

from datetime import datetime, timedelta


def next_reminder(request: dict, delivery: dict, at: datetime) -> str | None:
    """Schedule one future attempt, never catch up missed intervals."""
    interval = request.get("reminder_interval", 0)
    limit = request.get("reminder_limit", 0)
    if not interval or delivery.get("reminder_count", 0) >= limit:
        return None
    return (at + timedelta(seconds=interval)).isoformat()


def reminder_due(request: dict, delivery: dict, at: datetime) -> bool:
    """Only repeat previously successful mobile calls, never failed/unknown work."""
    deadline = delivery.get("next_reminder_at")
    return bool(
        request.get("reminder_interval", 0)
        and delivery.get("reminder_count", 0) < request.get("reminder_limit", 0)
        and delivery["channel"] == "mobile"
        and delivery["status"] in {"accepted", "received", "cleared"}
        and deadline
        and datetime.fromisoformat(deadline) <= at
    )
