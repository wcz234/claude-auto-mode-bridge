# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2026-05-08

### Fixed
- **Critical**: Hook now outputs `permissionDecision: "allow"` for auto-approved operations. Previously, allow rules exited silently (exit code 0, no stdout), causing Claude Code to fall back to its default permission flow (still prompting the user). This was the root cause of "效果几乎没有".
- **Critical**: LLM fallback no longer crashes when `prompt` field is empty. Added a sensible default prompt that classifies tool calls as allow/deny.
- **Critical**: Removed the catch-all "Allow All Tools" rule that made the entire system a no-op. Replaced with specific allow rules for safe operations.
- Added `authorization: Bearer` header alongside `x-api-key` for broader proxy compatibility.

### Added
- 11 specific allow rules for safe operations (read-only tools, git read-only, build/test, project file edits, etc.)
- 13 deny rules covering dangerous operations (was 5): git force push, curl-pipe-to-shell, sudo, chmod 777, database destruction, .env file writes, agent config writes, system path writes
- Default LLM classification prompt with clear allow/deny criteria
- `format_allow_output()` function for explicit auto-approval

### Changed
- LLM fallback is now **enabled by default** (`"enabled": true`)
- LLM fallback timeout reduced from 10s to 5s
- install.py uses `sys.executable` instead of hardcoded `python` for cross-platform compatibility

## [1.0.0] - 2026-05-04

### Added
- Initial release
- Local rule engine with allow + deny rules
- LLM fallback for ambiguous operations
- One-click install/uninstall scripts
- Support for MiMo, DeepSeek, OpenRouter, and any Anthropic-compatible backend
- Path-based safety checks (system dirs, package dirs, agent config)
- Cross-platform support (Windows, macOS, Linux)
