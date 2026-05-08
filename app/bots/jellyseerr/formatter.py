from typing import Any


STATUS_ICONS = {
    1: "⏳",  # pending
    2: "✅",  # approved
    3: "❌",  # declined
    4: "📥",  # available
    5: "🔄",  # processing
}

NOTIFICATION_ICONS = {
    "MEDIA_PENDING": "⏳",
    "MEDIA_APPROVED": "✅",
    "MEDIA_DECLINED": "❌",
    "MEDIA_AVAILABLE": "🎉",
    "MEDIA_FAILED": "💥",
    "TEST_NOTIFICATION": "🔔",
}


def format_webhook_event(data: dict[str, Any]) -> str | None:
    notification_type = data.get("notification_type", "")
    subject = data.get("subject", "")
    message = data.get("message", "")
    media = data.get("media", {}) or {}
    request = data.get("request", {}) or {}

    if notification_type == "TEST_NOTIFICATION":
        return "🔔 Jellyseerr webhook test received!"

    icon = NOTIFICATION_ICONS.get(notification_type, "📋")
    media_type = media.get("media_type", "").capitalize()
    title = subject or "Unknown"

    requester = ""
    if request:
        requested_by = request.get("requestedBy", {}) or {}
        username = requested_by.get("displayName") or requested_by.get("username", "")
        if username:
            requester = f" — requested by **{username}**"

    label = notification_type.replace("MEDIA_", "").replace("_", " ").title()
    msg = f"{icon} **{label}:** {title}{requester}"
    if message and message != subject:
        msg += f"\n> {message}"

    return msg


def format_search_results(results: list[dict[str, Any]]) -> str:
    if not results:
        return "No results found."

    lines = ["**Search results:**\n"]
    for i, item in enumerate(results[:8], 1):
        media_type = item.get("mediaType", "")
        title = item.get("title") or item.get("name", "Unknown")
        year = item.get("releaseDate", "") or item.get("firstAirDate", "")
        year = year[:4] if year else ""
        tmdb_id = item.get("id", "?")
        media_status = item.get("mediaInfo", {}) or {}
        status = media_status.get("status")

        icon = "🎬" if media_type == "movie" else "📺"
        status_str = ""
        if status:
            status_str = f" {STATUS_ICONS.get(status, '')}"

        year_str = f" ({year})" if year else ""
        lines.append(f"{i}. {icon} **{title}**{year_str} — `!request {media_type} {tmdb_id}`{status_str}")

    return "\n".join(lines)


def format_request_result(result: dict[str, Any]) -> str:
    status = result.get("status", 1)
    media = result.get("media", {}) or {}
    title = media.get("originalTitle") or media.get("originalName") or "Unknown"
    icon = STATUS_ICONS.get(status, "📋")
    return f"{icon} Request submitted for **{title}**."
