---
description: Install/configure the claude-statusline status bar
allowed-tools: [Read, Write, Edit, Bash]
---

# Setup Claude Statusline

Configure the Claude Code statusline to show account info, subscription rate limits, model, cost, and context usage.

## Instructions

1. Read the user's current `~/.claude/settings.json`
2. Determine the absolute path to this plugin's `scripts/statusline` package by resolving it relative to this command file's location. The package is at `../scripts/statusline` relative to this command file.
3. Update `~/.claude/settings.json` to set the `statusLine` configuration:

```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 <absolute-path-to-scripts/statusline>",
    "refreshInterval": 1000
  }
}
```

Preserve all existing settings (hooks, etc.) — only add/update the `statusLine` key.

5. Confirm to the user that setup is complete and the statusline will appear on the next prompt.

## Display Format

```
folder(branch) | email(Plan) | Model $cost | 5h:N%(Xh Ym) 7d:N%(Xd Yh) | Ctx:N%
```

## Data Sources

- **folder/branch**: git from workspace
- **email/plan**: Anthropic OAuth API (`/api/oauth/profile`)
- **model/cost/context**: Claude Code stdin JSON
- **5h/7d rate limits**: Anthropic OAuth API (`/api/oauth/usage`)
- **OAuth token**: macOS Keychain (`Claude Code-credentials`) or `~/.claude/.credentials.json`
