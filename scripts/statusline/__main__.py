"""
Claude Code Statusline
Shows: folder(branch) | email(plan) | model $cost | 5h:N% 7d:N% | Ctx:N%

Data sources:
  - stdin JSON: model, cost, context_window (from Claude Code)
  - Keychain + API: account email, plan, rate limits (from Anthropic OAuth)
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
from .display import R, color_for_percent, progress_bar, format_reset_time


def main():
    try:
        input_data = json.load(sys.stdin)

        # 1. folder(branch) | modified/staged/untracked
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
            folder = f"\033[36m{dir_name}{R}(\033[33m{branch}{R}{status_str})"
        else:
            folder = f"\033[36m{dir_name}{R}"

        # 2. account + model (+ optional cost)
        profile = fetch_profile()
        model = input_data.get("model", {}).get("display_name", "?")
        show_cost = os.environ.get("CLAUDE_STATUSLINE_SHOW_COST", "0") == "1"
        cost_str = ""
        if show_cost:
            cost = input_data.get("cost", {}).get("total_cost_usd", 0)
            cost_str = f" \033[37m${cost:.2f}{R}"
        if profile:
            acct = profile.get("account", {})
            email = acct.get("email", "?")
            plan = "Pro" if acct.get("has_claude_pro") else "Max" if acct.get("has_claude_max") else "Free"
            account_str = f"\033[35m{email}{R}(\033[90m{plan}, {model}{R}){cost_str}"
        else:
            account_str = f"\033[90m--{R}(\033[90m{model}{R}){cost_str}"

        # 4. rate limits (5h / 7d)
        usage = fetch_usage()
        rate_parts = []
        if usage:
            fh = usage.get("five_hour")
            if fh:
                pct = round(fh.get("utilization", 0))
                reset = format_reset_time(fh.get("resets_at"))
                label = f"session(\033[90m{reset}{R})" if reset else "session"
                rate_parts.append(f"{label}: {progress_bar(pct)}")
            sd = usage.get("seven_day")
            if sd:
                pct = round(sd.get("utilization", 0))
                reset = format_reset_time(sd.get("resets_at"))
                label = f"week(\033[90m{reset}{R})" if reset else "week"
                rate_parts.append(f"{label}: {progress_bar(pct)}")
        else:
            rate_parts.append(f"session: \033[90m{'░' * 10} --{R}")
            rate_parts.append(f"week: \033[90m{'░' * 10} --{R}")
        rate_str = " | ".join(rate_parts)

        # 5. context window
        ctx_pct = input_data.get("context_window", {}).get("used_percentage", 0)

        # Line 1: Claude Code section
        print(
            f"{account_str}"
            f" | {rate_str}"
        )
        # Line 2: Folder + context section
        print(f"{folder} | context: {progress_bar(ctx_pct)}")

    except Exception:
        print("Claude Code")


if __name__ == "__main__":
    main()
