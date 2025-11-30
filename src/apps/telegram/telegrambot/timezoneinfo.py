"""Timezone information for Telegram bot."""

import zoneinfo

ALL_TIMEZONES = zoneinfo.available_timezones()
COMMON_TIMEZONES = {
    "Europe": [
        "Europe/Brussels",
        "Europe/Paris",
        "Europe/Berlin",
        "Europe/London",
        "Europe/Madrid",
        "Europe/Rome",
        "Europe/Warsaw",
        "Europe/Moscow",
    ],
    "America": [
        "America/New_York",
        "America/Chicago",
        "America/Denver",
        "America/Los_Angeles",
        "America/Sao_Paulo",
        "America/Mexico_City",
    ],
    "Asia": [
        "Asia/Dubai",
        "Asia/Kolkata",
        "Asia/Bangkok",
        "Asia/Shanghai",
        "Asia/Tokyo",
        "Asia/Seoul",
    ],
    "Africa": [
        "Africa/Cairo",
        "Africa/Johannesburg",
        "Africa/Nairobi",
        "Africa/Lagos",
    ],
    "Pacific": [
        "Australia/Sydney",
        "Australia/Melbourne",
        "Pacific/Auckland",
        "Pacific/Honolulu",
    ],
}


def normalize_timezone(tz_input: str) -> str:
    """Normalize timezone input by stripping spaces and title-casing.

    For single word timezones like "UTC", convert to uppercase.

    Example:
        "america/new york" -> "America/New_York"
        " europe / paris " -> "Europe/Paris"
        "UTC" -> "UTC"
    """
    if "/" not in tz_input:
        # Single word timezone, e.g.: "UTC"
        return tz_input.strip().upper()
    return tz_input.strip().replace(" ", "_").title()
