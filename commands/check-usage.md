---
description: Show current Claude subscription usage and account info
allowed-tools: [Bash]
---

# Check Claude Usage

Display current subscription usage details.

## Instructions

Run the following command to fetch and display usage information:

```bash
TOKEN=$(security find-generic-password -s "Claude Code-credentials" -w 2>/dev/null | python3 -c "import json,sys; print(json.loads(sys.stdin.read()).get('claudeAiOauth',{}).get('accessToken',''))")

echo "=== Account ==="
curl -s -H "Accept: application/json" -H "Authorization: Bearer $TOKEN" -H "anthropic-beta: oauth-2025-04-20" "https://api.anthropic.com/api/oauth/profile" | python3 -c "
import json,sys
d=json.load(sys.stdin)
a=d.get('account',{})
o=d.get('organization',{})
print(f\"Email: {a.get('email','?')}\")
print(f\"Name: {a.get('display_name','?')}\")
plan='Pro' if a.get('has_claude_pro') else 'Max' if a.get('has_claude_max') else 'Free'
print(f\"Plan: {plan}\")
print(f\"Org: {o.get('name','?')}\")
print(f\"Extra Usage: {'Enabled' if o.get('has_extra_usage_enabled') else 'Disabled'}\")
"

echo ""
echo "=== Rate Limits ==="
curl -s -H "Accept: application/json" -H "Authorization: Bearer $TOKEN" -H "anthropic-beta: oauth-2025-04-20" "https://api.anthropic.com/api/oauth/usage" | python3 -c "
import json,sys
from datetime import datetime, timezone
d=json.load(sys.stdin)
def fmt(bucket, label):
    b=d.get(bucket)
    if not b: return
    pct=round(b.get('utilization',0))
    reset=b.get('resets_at','')
    remaining=''
    if reset:
        try:
            dt=datetime.fromisoformat(reset.replace('Z','+00:00'))
            diff=dt-datetime.now(timezone.utc)
            s=int(diff.total_seconds())
            if s>0:
                h,r=divmod(s,3600)
                m=r//60
                remaining=f' (resets in {h}h{m}m)'
        except: pass
    print(f'{label}: {pct}%{remaining}')

fmt('five_hour', '5-Hour')
fmt('seven_day', '7-Day')
fmt('seven_day_sonnet', '7-Day Sonnet')

eu=d.get('extra_usage',{})
if eu and eu.get('is_enabled'):
    used=eu.get('used_credits',0)
    limit=eu.get('monthly_limit',0)
    print(f'Extra Usage: \${used:.2f} / \${limit} monthly')
"
```

Format the output nicely and present it to the user.
