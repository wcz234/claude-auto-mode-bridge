#!/usr/bin/env python3
"""
Claude Auto Mode Bridge - Local Permission Classifier

A PreToolUse hook for Claude Code that acts as a local permission classifier,
enabling auto mode for non-Claude models (MiMo, DeepSeek, OpenRouter, etc.).

Replaces Anthropic's server-side auto mode classifier with a local rule engine
+ optional LLM fallback.

License: MIT
Repository: https://github.com/xpyqj/claude-auto-mode-bridge
"""

__version__ = "1.0.0"

import json
import os
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Optional, Tuple

# --- Constants ---
HOOK_DIR = Path(__file__).parent
RULES_FILE = HOOK_DIR / "rules.json"
EXIT_ALLOW = 0

# Cached rules (loaded once per invocation)
_rules_cache: Optional[Dict] = None


def load_rules() -> Dict:
    """Load rules from rules.json."""
    global _rules_cache
    if _rules_cache is not None:
        return _rules_cache
    try:
        with open(RULES_FILE, "r", encoding="utf-8") as f:
            _rules_cache = json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load rules: {e}", file=sys.stderr)
        _rules_cache = {"allow": [], "deny": [], "llm_fallback": {"enabled": False}}
    return _rules_cache


def get_project_root(cwd: str) -> str:
    """Get the project root (git repo root or cwd)."""
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, cwd=cwd, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip().replace("\\", "/")
    except Exception:
        pass
    return cwd.replace("\\", "/")


def normalize_path(p: str) -> str:
    """Normalize path separators to forward slash."""
    return os.path.abspath(p).replace("\\", "/")


def matches_regex(pattern: str, text: str) -> bool:
    """Check if regex pattern matches text."""
    try:
        return bool(re.search(pattern, text, re.IGNORECASE))
    except re.error:
        return False


def check_path_condition(path_check: str, file_path: str,
                         cwd: str, project_root: str) -> bool:
    """Check path-based conditions. Returns True if condition is MET."""
    if not file_path:
        return False

    norm_path = normalize_path(file_path)
    norm_project = normalize_path(project_root)
    home = normalize_path(os.path.expanduser("~"))

    if path_check == "in_project":
        norm_cwd = normalize_path(cwd)
        return norm_path.startswith(norm_project) or norm_path.startswith(norm_cwd)

    elif path_check == "in_memory_dir":
        memory_base = normalize_path(os.path.join(home, ".claude", "projects"))
        return memory_base in norm_path and "/memory/" in norm_path

    elif path_check == "is_system_path":
        system_prefixes = [
            "/etc/", "/usr/", "/System/", "/Windows/", "/Program Files/",
            "/ProgramData/", "/boot/", "/sbin/", "/lib/", "/lib64/",
            "C:/Windows/", "C:/Program Files/", "C:/Program Files (x86)/",
            "C:/ProgramData/",
        ]
        sensitive_home = [
            normalize_path(os.path.join(home, ".ssh")),
            normalize_path(os.path.join(home, ".gnupg")),
            normalize_path(os.path.join(home, ".aws")),
            normalize_path(os.path.join(home, ".config")),
        ]
        for prefix in system_prefixes:
            if norm_path.startswith(prefix.lower()) or norm_path.startswith(prefix):
                return True
        for sh in sensitive_home:
            if norm_path.startswith(sh):
                return True
        return False

    elif path_check == "is_agent_config":
        agent_config_paths = ["/.claude/settings", "/CLAUDE.md"]
        for acp in agent_config_paths:
            if acp in norm_path:
                return True
        return False

    elif path_check == "is_package_dir":
        package_dirs = [
            "/node_modules/", "/site-packages/", "/vendor/", "/.venv/",
            "/pnpm-store/", "/.yarn/", "/.cache/", "/__pycache__/",
            "/bower_components/", "/.gradle/", "/.m2/",
        ]
        for pd in package_dirs:
            if pd in norm_path:
                return True
        return False

    return False


def extract_file_path(tool_name: str, tool_input: Dict) -> Optional[str]:
    """Extract file path from tool input based on tool type."""
    if tool_name in ("Write", "Edit", "Read", "MultiEdit"):
        return tool_input.get("file_path", "")
    elif tool_name == "NotebookEdit":
        return tool_input.get("notebook_path", "")
    return None


def check_allow_rule(rule: Dict, tool_name: str, tool_input: Dict,
                     cwd: str, project_root: str) -> bool:
    """Check if an allow rule matches. Returns True to allow."""
    tools = rule.get("tools", [])
    if tools and tool_name not in tools:
        return False

    pattern = rule.get("pattern")
    if pattern:
        command = tool_input.get("command", "")
        if not matches_regex(pattern, command):
            return False
        allow_if = rule.get("allow_if_contains")
        if allow_if:
            return any(af in command for af in allow_if)

    path_check = rule.get("path_check")
    if path_check:
        file_path = extract_file_path(tool_name, tool_input)
        if not check_path_condition(path_check, file_path or "", cwd, project_root):
            return False

    return True


def check_deny_rule(rule: Dict, tool_name: str, tool_input: Dict,
                    cwd: str, project_root: str) -> bool:
    """Check if a deny rule matches. Returns True to deny."""
    tools = rule.get("tools", [])
    if tools and tool_name not in tools:
        return False

    pattern = rule.get("pattern")
    if pattern:
        command = tool_input.get("command", "")
        if not matches_regex(pattern, command):
            return False

    path_check = rule.get("path_check")
    if path_check:
        file_path = extract_file_path(tool_name, tool_input)
        if not check_path_condition(path_check, file_path or "", cwd, project_root):
            return False

    return True


def llm_classify(tool_name: str, tool_input: Dict,
                 cwd: str, rules: Dict) -> Tuple[str, str]:
    """Use LLM to classify ambiguous operations. Returns (decision, reason)."""
    llm_config = rules.get("llm_fallback", {})
    if not llm_config.get("enabled", False):
        return "allow", "No LLM fallback configured"

    prompt_template = llm_config.get("prompt", "")
    prompt = prompt_template.format(
        tool_name=tool_name,
        tool_input=json.dumps(tool_input, ensure_ascii=False)[:2000],
        cwd=cwd
    )

    base_url = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    api_key = os.environ.get("ANTHROPIC_AUTH_TOKEN",
                             os.environ.get("ANTHROPIC_API_KEY", ""))
    model = os.environ.get(
        "ANTHROPIC_DEFAULT_HAIKU_MODEL",
        os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"))

    if not api_key:
        return "allow", "No API key available"

    timeout = llm_config.get("timeout_seconds", 10)
    try:
        url = f"{base_url.rstrip('/')}/v1/messages"
        payload = json.dumps({
            "model": model,
            "max_tokens": 100,
            "messages": [{"role": "user", "content": prompt}]
        }).encode("utf-8")

        req = urllib.request.Request(
            url, data=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            text = result.get("content", [{}])[0].get("text", "")
            json_match = re.search(r'\{[^}]*"decision"[^}]*\}', text)
            if json_match:
                parsed = json.loads(json_match.group())
                decision = parsed.get("decision", "allow").lower()
                reason = parsed.get("reason", "LLM classification")
                if decision in ("allow", "deny"):
                    return decision, reason
            return "allow", "LLM response not parseable"

    except urllib.error.HTTPError as e:
        return "allow", f"LLM API error ({e.code})"
    except Exception as e:
        return "allow", f"LLM call failed: {str(e)[:80]}"


def format_deny_output(reason: str) -> str:
    """Format JSON output for denying a tool call."""
    return json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason
        },
        "systemMessage": f"[Auto Mode] Blocked: {reason}"
    })


def main():
    """Main entry point for the PreToolUse hook."""
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(EXIT_ALLOW)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    cwd = input_data.get("cwd", os.getcwd())

    if not tool_name:
        sys.exit(EXIT_ALLOW)

    rules = load_rules()
    project_root = get_project_root(cwd)

    # Phase 1: Deny rules (safety-first)
    for rule in rules.get("deny", []):
        if check_deny_rule(rule, tool_name, tool_input, cwd, project_root):
            print(format_deny_output(
                rule.get("reason", "Denied by auto mode rule")),
                file=sys.stdout)
            sys.exit(EXIT_ALLOW)

    # Phase 2: Allow rules
    for rule in rules.get("allow", []):
        if check_allow_rule(rule, tool_name, tool_input, cwd, project_root):
            sys.exit(EXIT_ALLOW)

    # Phase 3: LLM fallback
    decision, reason = llm_classify(tool_name, tool_input, cwd, rules)
    if decision == "deny":
        print(format_deny_output(reason), file=sys.stdout)
    sys.exit(EXIT_ALLOW)


if __name__ == "__main__":
    main()
