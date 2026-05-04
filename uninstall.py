#!/usr/bin/env python3
"""Uninstall Claude Auto Mode Bridge from Claude Code settings."""

import json
import shutil
import sys
from pathlib import Path

BRIDGE_DIR_NAME = "auto-mode-bridge"
CLAUDE_DIR = Path.home() / ".claude"
SETTINGS_FILE = CLAUDE_DIR / "settings.json"
BRIDGE_DIR = CLAUDE_DIR / BRIDGE_DIR_NAME


def uninstall():
    print("=" * 50)
    print("  Claude Auto Mode Bridge - Uninstaller")
    print("=" * 50)
    print()

    # Step 1: Remove hook from settings.json
    print(f"[1/2] Removing hook from {SETTINGS_FILE} ...")
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)

            if "hooks" in settings and "PreToolUse" in settings["hooks"]:
                original_count = len(settings["hooks"]["PreToolUse"])
                settings["hooks"]["PreToolUse"] = [
                    h for h in settings["hooks"]["PreToolUse"]
                    if not any(
                        BRIDGE_DIR_NAME in (hook.get("command", ""))
                        for hook in h.get("hooks", [])
                    )
                ]
                removed = original_count - len(settings["hooks"]["PreToolUse"])

                # Clean up empty hooks dict
                if not settings["hooks"]["PreToolUse"]:
                    del settings["hooks"]["PreToolUse"]
                if not settings.get("hooks"):
                    settings.pop("hooks", None)

                with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                    json.dump(settings, f, indent=2, ensure_ascii=False)

                print(f"      Removed {removed} hook(s)")
            else:
                print("      No hooks found")
        except Exception as e:
            print(f"      Error: {e}")
    else:
        print("      settings.json not found")

    # Step 2: Remove bridge directory
    print(f"[2/2] Removing {BRIDGE_DIR} ...")
    if BRIDGE_DIR.exists():
        shutil.rmtree(str(BRIDGE_DIR))
        print("      Done")
    else:
        print("      Directory not found")

    print()
    print("Uninstall complete.")
    print("Restart Claude Code for changes to take effect.")


if __name__ == "__main__":
    uninstall()
