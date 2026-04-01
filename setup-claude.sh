#!/bin/bash
# Run this once on any new machine to configure Claude Code permissions.
# Usage: bash setup-claude.sh

SETTINGS="$HOME/.claude/settings.json"
mkdir -p "$HOME/.claude"

cat > "$SETTINGS" << 'EOF'
{
  "permissions": {
    "defaultMode": "bypassPermissions"
  }
}
EOF

echo "✓ Claude Code permissions configured at $SETTINGS"
echo "  Restart Claude Code to apply."
