from __future__ import annotations

from datetime import date, datetime, time, timezone


def parse_utc_to_local(value):
    """Parse UTC-like values and return system-local datetime for display."""
    if not value:
        return None

    # Plain date values are treated as local calendar dates and not shifted.
    if isinstance(value, date) and not isinstance(value, datetime):
        return datetime.combine(value, time.min)

    dt = None
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        if len(raw) == 10:
            try:
                return datetime.strptime(raw, "%Y-%m-%d")
            except ValueError:
                pass
        if raw.endswith("Z"):
            raw = f"{raw[:-1]}+00:00"
        try:
            dt = datetime.fromisoformat(raw)
        except ValueError:
            formats = (
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
            )
            for fmt in formats:
                try:
                    dt = datetime.strptime(raw, fmt)
                    break
                except ValueError:
                    continue
    if dt is None:
        return None

    # Naive datetimes persisted in DB are interpreted as UTC.
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone()

