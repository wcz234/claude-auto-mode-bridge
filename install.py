#!/usr/bin/env python3
"""Install Claude Auto Mode Bridge into Claude Code settings."""

import json
import os
import shutil
import sys
from pathlib import Path

BRIDGE_DIR_NAME = "auto-mode-bridge"
CLAUDE_DIR = Path.home() / ".claude"
SETTINGS_FILE = CLAUDE_DIR / "settings.json"
BRIDGE_DIR = CLAUDE_DIR / BRIDGE_DIR_NAME


def get_hook_dir():
    """Get the source directory (where this script lives)."""
    return Path(__file__).parent.resolve()


def install():
    print("=" * 50)
    print("  Claude Auto Mode Bridge - Installer")
    print("=" * 50)
    print()

    source_dir = get_hook_dir()

    # Step 1: Copy files to ~/.claude/auto-mode-bridge/
    print(f"[1/3] Copying files to {BRIDGE_DIR} ...")
    if BRIDGE_DIR.exists():
        shutil.rmtree(BRIDGE_DIR)
    shutil.copytree(str(source_dir), str(BRIDGE_DIR),
                    ignore=shutil.ignore_patterns(
                        '.git', '__pycache__', '*.pyc',
                        'install.py', 'uninstall.py',
                        'README.md', 'CONTRIBUTING.md',
                        'CHANGELOG.md', 'LICENSE',
                        'examples', '.github'))
    print(f"      Copied classifier.py + rules.json")

    # Step 2: Update settings.json
    print(f"[2/3] Updating {SETTINGS_FILE} ...")
    settings = {}
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except json.JSONDecodeError:
            print("      Warning: settings.json is invalid, creating new one")

    # Add or update the hook
    classifier_path = str(BRIDGE_DIR / "classifier.py").replace("\\", "/")
    hook_entry = {
        "matcher": "*",
        "hooks": [
            {
                "type": "command",
                "command": f"{sys.executable} {classifier_path}",
                "timeout": 15
            }
        ]
    }

    if "hooks" not in settings:
        settings["hooks"] = {}
    if "PreToolUse" not in settings["hooks"]:
        settings["hooks"]["PreToolUse"] = []

    # Remove any existing auto-mode-bridge hooks
    settings["hooks"]["PreToolUse"] = [
        h for h in settings["hooks"]["PreToolUse"]
        if not any(
            BRIDGE_DIR_NAME in (hook.get("command", ""))
            for hook in h.get("hooks", [])
        )
    ]

    # Add the new hook
    settings["hooks"]["PreToolUse"].append(hook_entry)

    # Write settings
    CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
    print("      Hook registered in PreToolUse")

    # Step 3: Verify
    print("[3/3] Verifying installation ...")
    classifier_exists = (BRIDGE_DIR / "classifier.py").exists()
    rules_exists = (BRIDGE_DIR / "rules.json").exists()
    hook_configured = any(
        BRIDGE_DIR_NAME in str(h)
        for h in settings.get("hooks", {}).get("PreToolUse", [])
    )

    all_ok = classifier_exists and rules_exists and hook_configured
    print(f"      classifier.py:  {'OK' if classifier_exists else 'MISSING'}")
    print(f"      rules.json:     {'OK' if rules_exists else 'MISSING'}")
    print(f"      Hook configured: {'OK' if hook_configured else 'MISSING'}")

    print()
    if all_ok:
        print("Installation complete!")
        print()
        print("Auto mode is now active for all Claude Code sessions.")
        print(f"Rules: {BRIDGE_DIR / 'rules.json'}")
        print(f"Hook:  {BRIDGE_DIR / 'classifier.py'}")
        print()
        print("To uninstall: python uninstall.py")
    else:
        print("Installation had issues. Check the output above.")
        sys.exit(1)


if __name__ == "__main__":
    install()
