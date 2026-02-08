# claude-statusline

Claude Code statusline plugin that shows account info, subscription rate limits, model, cost, and context usage.

```
jinhong@gmail.com(Max, Opus 4.6) | session: ██░░░░░░░░ 15% | week: ░░░░░░░░░░ 2%
my-project(main +3 !1 ?2) | context: ██████░░░░ 58%
```

## Requirements

- Python 3
- Claude Code CLI with plugin support
- Anthropic OAuth (Claude Pro/Max subscription)

## Install

```bash
claude install-plugin /path/to/claude-statusline-plugin
```

Or clone and install:

```bash
git clone https://github.com/gnongs/claude-statusline-plugin.git
claude install-plugin ./claude-statusline-plugin
```

After installing, run the setup command inside Claude Code:

```
/setup
```

This will configure `~/.claude/settings.json` automatically.

### Manual Setup

Add the following to `~/.claude/settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 /path/to/claude-statusline-plugin/scripts/statusline",
    "refreshInterval": 1000
  }
}
```

## Display

**Line 1** — Account & rate limits:

| Section | Description |
|---------|-------------|
| `email(Plan, Model)` | Account email, subscription plan (Pro/Max/Free), active model |
| `session: ██░░ N%` | 5-hour rolling rate limit with reset time |
| `week: ██░░ N%` | 7-day rolling rate limit with reset time |

**Line 2** — Workspace & context:

| Section | Description |
|---------|-------------|
| `folder(branch +S !M ?U)` | Directory, git branch, staged/modified/untracked counts |
| `context: ██░░ N%` | Context window usage |

Colors: green (< 70%), yellow (70-89%), red (90%+)

## Commands

| Command | Description |
|---------|-------------|
| `/setup` | Install and configure the statusline |
| `/check-usage` | Show detailed account and rate limit info |
| `/uninstall` | Remove the statusline from settings |

## Options

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `CLAUDE_STATUSLINE_SHOW_COST` | `0` | Set to `1` to show session cost (`$0.15`) |

## Data Sources

- **Account/Plan**: Anthropic OAuth API (`/api/oauth/profile`)
- **Rate limits**: Anthropic OAuth API (`/api/oauth/usage`)
- **Model/Cost/Context**: Claude Code stdin JSON
- **OAuth token**: macOS Keychain (`Claude Code-credentials`) or `~/.claude/.credentials.json`
- **Git**: Local git commands

API responses are cached in `/tmp/claude_statusline/` (usage: 60s, profile: 1h).

## Project Structure

```
.claude-plugin/
  plugin.json           # Plugin metadata
commands/
  setup.md              # /setup command
  check-usage.md        # /check-usage command
  uninstall.md          # /uninstall command
scripts/
  statusline/
    __init__.py
    __main__.py          # Entry point + main()
    api.py               # OAuth, API calls, caching
    display.py           # ANSI colors, progress bar, time formatting
    git.py               # Git branch & status
```
