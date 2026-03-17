from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
except ImportError:
    ZoneInfo = None

    class ZoneInfoNotFoundError(Exception):
        pass


def _get_ist_timezone():
    if ZoneInfo is not None:
        try:
            return ZoneInfo("Asia/Kolkata")
        except ZoneInfoNotFoundError:
            pass

    return timezone(timedelta(hours=5, minutes=30), name="IST")


IST = _get_ist_timezone()


def now_ist():
    return datetime.now(IST)


def now_ist_naive():
    return now_ist().replace(tzinfo=None)


def now_ist_iso():
    return now_ist().isoformat()


def ensure_ist(value):
    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=IST)

    return value.astimezone(IST)


def to_ist_iso(value):
    normalized = ensure_ist(value)
    return normalized.isoformat() if normalized is not None else None
