"""
Claude Code Statusline
Line 1: email(model)
Line 2: session(Xh) bar% | week(MM/DD) bar% | ctx bar%
Line 3: folder(branch +S !M ?U)

Data sources:
  - stdin JSON: model, cost, context_window, rate_limits (from Claude Code)
  - Keychain + API: account email (from Anthropic OAuth)
"""
import json
import os
import sys

# Allow running as `python3 path/to/statusline` (directory execution)
if not __package__:
    _parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, _parent)
    import importlib
    __package__ = "statusline"
    __spec__ = importlib.util.find_spec(__package__)

from .git import get_git_info
from .api import fetch_usage, fetch_profile
from .display import R, progress_bar, format_reset_hours, format_reset_date, fmt_pct


def main():
    try:
        input_data = json.load(sys.stdin)

        # Line 1: email(model)
        profile = fetch_profile()
        model = input_data.get("model", {}).get("display_name", "?")
        cost_str = ""
        if os.environ.get("CLAUDE_STATUSLINE_SHOW_COST", "0") == "1":
            cost = input_data.get("cost", {}).get("total_cost_usd", 0)
            cost_str = f" \033[37m${cost:.2f}{R}"
        if profile:
            email = profile.get("account", {}).get("email", "?")
            line1 = f"\033[35m{email}{R}(\033[90m{model}{R}){cost_str}"
        else:
            line1 = f"\033[90m{model}{R}{cost_str}"

        # Line 2: session(Xh) bar% | week(MM/DD) bar% | ctx bar%
        usage = fetch_usage()
        rate_parts = []
        if usage:
            fh = usage.get("five_hour")
            if fh:
                pct = fmt_pct(fh.get("utilization", 0))
                reset = format_reset_hours(fh.get("resets_at"))
                label = f"session(\033[90m{reset}{R})" if reset else "session"
                rate_parts.append(f"{label} {progress_bar(pct)}")
            sd = usage.get("seven_day")
            if sd:
                pct = fmt_pct(sd.get("utilization", 0))
                reset = format_reset_date(sd.get("resets_at"))
                label = f"week(\033[90m{reset}{R})" if reset else "week"
                rate_parts.append(f"{label} {progress_bar(pct)}")
        else:
            rate_parts.append(f"session \033[90m{'░' * 10} --{R}")
            rate_parts.append(f"week \033[90m{'░' * 10} --{R}")
        ctx_used = input_data.get("context_window", {}).get("used_percentage", 0)
        rate_parts.append(f"ctx {progress_bar(ctx_used)}")
        line2 = " | ".join(rate_parts)

        # Line 3: folder(branch +S !M ?U)
        cwd = input_data.get("workspace", {}).get("current_dir", "~")
        dir_name = os.path.basename(cwd)
        branch, staged, modified, untracked = get_git_info(cwd)
        if branch:
            git_stats = []
            if staged:
                git_stats.append(f"\033[32m+{staged}{R}")
            if modified:
                git_stats.append(f"\033[31m!{modified}{R}")
            if untracked:
                git_stats.append(f"\033[90m?{untracked}{R}")
            status_str = f" {' '.join(git_stats)}" if git_stats else ""
            line3 = f"\033[36m{dir_name}{R}(\033[33m{branch}{R}{status_str})"
        else:
            line3 = f"\033[36m{dir_name}{R}"

        print(line1)
        print(line2)
        print(line3)

    except Exception:
        print("Claude Code")


if __name__ == "__main__":
    main()
