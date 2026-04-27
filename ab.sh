#!/usr/bin/env bash
# OpenCode A/B test runner — uses OPENCODE_CONFIG env var
# Usage: ./ab.sh <variant>
#   variant: glm | deepseek

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VARIANT="${1:-}"

if [[ -z "$VARIANT" ]]; then
  echo "Usage: $0 <glm|deepseek>"
  exit 1
fi

CONFIG_FILE="$SCRIPT_DIR/$VARIANT.json"
if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "Error: config '$CONFIG_FILE' not found"
  exit 1
fi

# Show prompt
echo ""
echo "═══════════ PASTE THIS INTO OPENCODE ═══════════"
sed -n '/^```$/,/^```$/p' "$SCRIPT_DIR/test-prompt.md" | head -20 | sed '1d;$d'
echo "════════════════════════════════════════════════"
echo ""

# Launch OpenCode with variant config
exec env OPENCODE_CONFIG="$CONFIG_FILE" opencode
