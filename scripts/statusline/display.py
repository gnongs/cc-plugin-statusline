R = "\033[0m"


def color_for_percent(pct):
    if pct >= 90:
        return "\033[31m"
    if pct >= 70:
        return "\033[33m"
    return "\033[32m"


def progress_bar(pct, width=10):
    filled = round(pct / 100 * width)
    filled = max(0, min(width, filled))
    c = color_for_percent(pct)
    return f"{c}{'█' * filled}\033[90m{'░' * (width - filled)}{R} {c}{pct}%{R}"


def format_reset_time(resets_at):
    if not resets_at:
        return ""
    try:
        from datetime import datetime, timezone
        reset_dt = datetime.fromisoformat(resets_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        if (reset_dt - now).total_seconds() <= 0:
            return ""
        local_dt = reset_dt.astimezone().replace(microsecond=0)
        return local_dt.strftime("%Y-%m-%dT%H:%M:%S %Z")
    except Exception:
        return ""
