"""Clock times for weekly hours and time off (2026-11-02, user's call).

An end time of 12:00 AM (00:00) means midnight at the END of that day, so an
RND can work "10 PM to 12 AM". Use these helpers wherever an end time is
compared or turned into a datetime: a plain `time` comparison would read
00:00 as the start of the day."""

from datetime import datetime, time, timedelta

MIDNIGHT = time(0)
DAY_MINUTES = 24 * 60


def clean_availability_blocks(value):
    """[{day_of_week, start_time "HH:MM", end_time "HH:MM"}, ...] -> [(day, start, end)].
    Each block at least an hour (one session), no overlaps per day. Raises a
    DRF ValidationError, so serializers can call it from a validate_ method."""
    from rest_framework import serializers

    if not value:
        return []
    if len(value) > 50:
        raise serializers.ValidationError("Too many availability blocks.")
    blocks = []
    for item in value:
        try:
            day = int(item["day_of_week"])
            start = datetime.strptime(str(item["start_time"])[:5], "%H:%M").time()
            end = datetime.strptime(str(item["end_time"])[:5], "%H:%M").time()
        except (KeyError, TypeError, ValueError):
            raise serializers.ValidationError("Each availability block needs a day, a start time and an end time.")
        if not 0 <= day <= 6:
            raise serializers.ValidationError("Invalid day of the week.")
        if end_minutes(end) - start_minutes(start) < 60:  # 12:00 AM end = midnight
            raise serializers.ValidationError("Each availability block must be at least 1 hour long (one consultation).")
        blocks.append((day, start, end))
    for day in range(7):
        same_day = sorted((b for b in blocks if b[0] == day), key=lambda b: b[1])
        for prev, nxt in zip(same_day, same_day[1:]):
            if start_minutes(nxt[1]) < end_minutes(prev[2]):
                raise serializers.ValidationError("Two availability blocks on the same day overlap.")
    return blocks


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
