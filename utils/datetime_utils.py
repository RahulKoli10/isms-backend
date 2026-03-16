from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
except ImportError:  # pragma: no cover
    ZoneInfo = None

    class ZoneInfoNotFoundError(Exception):
        pass


def _get_ist_timezone():
    if ZoneInfo is not None:
        try:
            return ZoneInfo("Asia/Kolkata")
        except ZoneInfoNotFoundError:
            pass

    # Fallback for Windows/Python environments without tzdata installed.
    return timezone(timedelta(hours=5, minutes=30), name="IST")


IST = _get_ist_timezone()


def now_ist():
    return datetime.now(IST)


def now_ist_iso():
    return now_ist().isoformat()
