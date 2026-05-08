from typing import Any


def format_event(data: dict[str, Any]) -> str | None:
    notification_type = data.get("NotificationType", "")

    if notification_type in ("ItemAdded", "MediaAdded"):
        return _format_media_added(data)
    if notification_type == "PlaybackStart":
        return _format_playback(data, "started watching")
    if notification_type == "PlaybackStop":
        return _format_playback(data, "finished watching")
    if notification_type == "UserCreated":
        username = data.get("NotificationUsername") or data.get("Username", "Someone")
        return f"👤 New user joined: **{username}**"

    return None


def _format_media_added(data: dict[str, Any]) -> str:
    item_type = data.get("ItemType", "")
    name = data.get("Name") or data.get("ItemName", "Unknown")
    year = data.get("Year", "")
    series = data.get("SeriesName", "")
    season = data.get("SeasonNumber")
    episode = data.get("EpisodeNumber")
    overview = data.get("Overview", "")

    if item_type in ("Episode",) and series:
        title = f"{series}"
        if season is not None and episode is not None:
            title += f" S{int(season):02d}E{int(episode):02d}"
        title += f" — {name}"
        icon = "📺"
    elif item_type == "Movie":
        title = f"{name} ({year})" if year else name
        icon = "🎬"
    elif item_type == "Audio":
        artist = data.get("Artist", "")
        album = data.get("Album", "")
        title = f"{name}"
        if artist:
            title = f"{artist} — {title}"
        if album:
            title += f" ({album})"
        icon = "🎵"
    else:
        title = f"{name} ({year})" if year else name
        icon = "📦"

    msg = f"{icon} **New {item_type or 'item'} added:** {title}"
    if overview:
        short = overview[:200] + ("…" if len(overview) > 200 else "")
        msg += f"\n> {short}"
    return msg


def _format_playback(data: dict[str, Any], action: str) -> str:
    user = data.get("NotificationUsername") or data.get("Username", "Someone")
    name = data.get("Name") or data.get("ItemName", "something")
    series = data.get("SeriesName", "")
    season = data.get("SeasonNumber")
    episode = data.get("EpisodeNumber")

    if series:
        title = series
        if season is not None and episode is not None:
            title += f" S{int(season):02d}E{int(episode):02d}"
        title += f" — {name}"
    else:
        title = name

    return f"▶️ **{user}** {action} **{title}**"
