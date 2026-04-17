import os
import shutil
from dataclasses import dataclass

R = "\033[0m"


def fmt_pct(u):
    """Floor to int but cap sub-100% values at 99 so only true saturation shows 100%."""
    try:
        u = float(u)
    except (TypeError, ValueError):
        return 0
    if u >= 100:
        return 100
    if u <= 0:
        return 0
    return min(int(u), 99)


def color_for_percent(pct):
    if pct >= 90:
        return "\033[31m"
    if pct >= 70:
        return "\033[33m"
    return "\033[32m"


def progress_bar(pct, width=10):
    c = color_for_percent(pct)
    if width <= 0:
        return f"{c}{pct}%{R}"
    filled = int(pct / 100 * width)
    filled = max(0, min(width, filled))
    return f"{c}{'█' * filled}\033[90m{'░' * (width - filled)}{R} {c}{pct}%{R}"


@dataclass
class TierConfig:
    bar_width: int
    show_reset: bool
    show_email: bool
    email_full: bool
    rate_label_session: str
    rate_label_week: str
    ctx_label: str
    show_git_stats: bool


def get_tier_config(width):
    if width >= 130:
        return TierConfig(10, True, True, True, "session", "week", "context", True)
    if width >= 100:
        return TierConfig(8, False, True, True, "session", "week", "context", True)
    if width >= 75:
        return TierConfig(6, False, True, False, "5h", "7d", "ctx", True)
    if width >= 55:
        return TierConfig(4, False, False, False, "5h", "7d", "ctx", False)
    return TierConfig(0, False, False, False, "5h", "7d", "ctx", False)


def get_terminal_width(stdin_width=None):
    # 1. stdin JSON width (passed from Claude Code)
    if stdin_width and isinstance(stdin_width, (int, float)) and stdin_width > 0:
        return int(stdin_width)
    # 2. User override env var
    for var in ('CLAUDE_STATUSLINE_WIDTH', 'COLUMNS'):
        val = os.environ.get(var)
        if val:
            try:
                return int(val)
            except ValueError:
                pass
    # 3. /dev/tty ioctl
    try:
        import fcntl, termios, struct
        with open('/dev/tty', 'r') as tty:
            result = fcntl.ioctl(tty.fileno(), termios.TIOCGWINSZ, b'\x00' * 8)
            return struct.unpack('HHHH', result)[1]
    except Exception:
        pass
    # 4. stderr fd / shutil fallback
    try:
        return os.get_terminal_size(2).columns
    except (OSError, ValueError):
        pass
    try:
        return shutil.get_terminal_size((120, 24)).columns
    except Exception:
        return 120


def _parse_reset_dt(resets_at):
    """Parse resets_at as datetime (handles both Unix timestamp and ISO string)."""
    from datetime import datetime, timezone
    if isinstance(resets_at, (int, float)):
        return datetime.fromtimestamp(resets_at, tz=timezone.utc)
    return datetime.fromisoformat(str(resets_at).replace("Z", "+00:00"))


def format_reset_hours(resets_at):
    """Format reset time as hours/minutes remaining (e.g., '3h', '45m')."""
    if not resets_at:
        return ""
    try:
        from datetime import datetime, timezone
        remaining = (_parse_reset_dt(resets_at) - datetime.now(timezone.utc)).total_seconds()
        if remaining <= 0:
            return ""
        hours = int(remaining / 3600)
        if hours > 0:
            return f"{hours}h"
        return f"{int(remaining / 60)}m"
    except Exception:
        return ""


def format_reset_date(resets_at):
    """Format reset time as local date (e.g., '04/16')."""
    if not resets_at:
        return ""
    try:
        from datetime import datetime, timezone
        reset_dt = _parse_reset_dt(resets_at)
        if (reset_dt - datetime.now(timezone.utc)).total_seconds() <= 0:
            return ""
        return reset_dt.astimezone().strftime("%m/%d")
    except Exception:
        return ""


def format_reset_time(resets_at):
    if not resets_at:
        return ""
    try:
        from datetime import datetime, timezone
        reset_dt = _parse_reset_dt(resets_at)
        now = datetime.now(timezone.utc)
        if (reset_dt - now).total_seconds() <= 0:
            return ""
        local_dt = reset_dt.astimezone().replace(microsecond=0)
        return local_dt.strftime("%Y-%m-%dT%H:%M:%S %Z")
    except Exception:
        return ""
