#!/bin/bash
# Deploy web4 governance plugin for Claude Code
# Run this on each machine in the collective

set -e

# Determine paths based on platform
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if [[ -d "/home/dp/ai-workspace" ]]; then
        PLUGIN_PATH="/home/dp/ai-workspace/web4/claude-code-plugin"
    else
        PLUGIN_PATH="$(cd "$(dirname "$0")" && pwd)"
    fi
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || -n "$WSL_DISTRO_NAME" ]]; then
    PLUGIN_PATH="/mnt/c/exe/projects/ai-agents/web4/claude-code-plugin"
else
    PLUGIN_PATH="$(cd "$(dirname "$0")" && pwd)"
fi

echo "=== Web4 Governance Plugin Deployment ==="
echo "Plugin path: $PLUGIN_PATH"
echo ""

# Step 1: Create ~/.web4 directory structure
echo "[1/4] Creating ~/.web4 directory..."
mkdir -p ~/.web4/sessions ~/.web4/r6 ~/.web4/audit
chmod 700 ~/.web4

# Step 2: Create default preferences
echo "[2/4] Creating preferences..."
if [[ ! -f ~/.web4/preferences.json ]]; then
    cat > ~/.web4/preferences.json << 'EOF'
{
  "audit_level": "standard",
  "show_r6_status": true,
  "action_budget": null
}
EOF
    echo "  Created ~/.web4/preferences.json"
else
    echo "  Preferences already exist, skipping"
fi

# Step 3: Make hooks executable
echo "[3/4] Making hooks executable..."
chmod +x "$PLUGIN_PATH/hooks/"*.py
echo "  Done"

# Step 4: Show hook configuration for settings.json
echo "[4/4] Hook configuration for Claude Code..."
echo ""
echo "Add this to your project's .claude/settings.local.json or ~/.claude/settings.json:"
echo ""
cat << EOF
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$PLUGIN_PATH/hooks/session_start.py"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "$PLUGIN_PATH/hooks/pre_tool_use.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "$PLUGIN_PATH/hooks/post_tool_use.py"
          }
        ]
      }
    ]
  }
}
EOF

echo ""
echo "=== Deployment complete ==="
echo ""
echo "Next steps:"
echo "1. Add the hook configuration above to your Claude Code settings"
echo "2. Restart Claude Code"
echo "3. Check ~/.web4/sessions/ for session state files"
echo ""
echo "To verify: Run 'claude --debug' and look for hook execution logs"
