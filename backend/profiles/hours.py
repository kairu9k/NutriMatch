"""Clock times for weekly hours and time off (2026-11-02, user's call).

An end time of 12:00 AM (00:00) means midnight at the END of that day, so an
RND can work "10 PM to 12 AM". Use these helpers wherever an end time is
compared or turned into a datetime: a plain `time` comparison would read
00:00 as the start of the day."""

from datetime import datetime, time, timedelta

MIDNIGHT = time(0)
DAY_MINUTES = 24 * 60


def start_minutes(t):
    return t.hour * 60 + t.minute


def end_minutes(t):
    """Minutes from the day's start to this END time; 12:00 AM is 1440."""
    return DAY_MINUTES if t == MIDNIGHT else t.hour * 60 + t.minute


def end_datetime(day, t, tz):
    """The END time on `day` as an aware datetime (12:00 AM is the next day's 00:00)."""
    at = datetime.combine(day, t, tzinfo=tz)
    return at + timedelta(days=1) if t == MIDNIGHT else at


def covers(block_start, block_end, local_start, local_end):
    """Does a block (start/end clock times) cover the span local_start..local_end
    (aware datetimes on the block's day)? The span may end at midnight."""
    day = local_start.date()
    lo = start_minutes(block_start)
    hi = end_minutes(block_end)
    a = start_minutes(local_start.time())
    b = (local_end.date() - day).days * DAY_MINUTES + start_minutes(local_end.time())
    return lo <= a and b <= hi
