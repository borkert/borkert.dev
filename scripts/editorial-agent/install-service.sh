#!/bin/bash
set -euo pipefail

# install-service.sh — Installs borkert.dev Daily Editorial Agent as a macOS LaunchAgent
# Target: Mac mini (or local machine)
# Scheduled to run nightly at 3:00 AM

PLIST_NAME="dev.borkert.daily-agent.plist"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_PLIST="$SCRIPT_DIR/$PLIST_NAME"
TARGET_DIR="$HOME/Library/LaunchAgents"
TARGET_PLIST="$TARGET_DIR/$PLIST_NAME"
LOG_DIR="$HOME/Library/Logs"

echo "=== Installing borkert.dev Daily Editorial Agent LaunchAgent ==="

mkdir -p "$TARGET_DIR" "$LOG_DIR"

if launchctl list | grep -q "dev.borkert.daily-agent"; then
    echo "Unloading existing LaunchAgent..."
    launchctl unload "$TARGET_PLIST" 2>/dev/null || true
fi

echo "Copying plist to $TARGET_PLIST..."
cp "$SOURCE_PLIST" "$TARGET_PLIST"
chmod 644 "$TARGET_PLIST"

echo "Loading LaunchAgent into launchctl..."
launchctl load "$TARGET_PLIST"

echo ""
echo "✓ Daily Editorial Agent installed successfully!"
echo "  - Schedule: Daily at 3:00 AM"
echo "  - Log: $LOG_DIR/borkert-editorial-agent.log"
echo "  - Error Log: $LOG_DIR/borkert-editorial-agent-error.log"
echo ""
echo "To test run immediately: launchctl start dev.borkert.daily-agent"
echo "To check status: launchctl list | grep dev.borkert.daily-agent"
