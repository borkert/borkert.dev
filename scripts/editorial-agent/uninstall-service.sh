#!/bin/bash
set -euo pipefail

# uninstall-service.sh — Unloads and removes the borkert.dev Daily Editorial Agent LaunchAgent

PLIST_NAME="dev.borkert.daily-agent.plist"
TARGET_DIR="$HOME/Library/LaunchAgents"
TARGET_PLIST="$TARGET_DIR/$PLIST_NAME"

echo "=== Uninstalling borkert.dev Daily Editorial Agent LaunchAgent ==="

if launchctl list | grep -q "dev.borkert.daily-agent"; then
    echo "Unloading LaunchAgent..."
    launchctl unload "$TARGET_PLIST" 2>/dev/null || true
fi

if [ -f "$TARGET_PLIST" ]; then
    echo "Removing $TARGET_PLIST..."
    rm -f "$TARGET_PLIST"
fi

echo "✓ Daily Editorial Agent uninstalled successfully."
