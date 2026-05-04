# Contributing

Contributions are welcome! Here's how to get started.

## Development

```bash
git clone https://github.com/wcz234/claude-auto-mode-bridge.git
cd claude-auto-mode-bridge
```

The project is a single Python file + a JSON rules file. No build step needed.

## Adding Rules

Edit `rules.json` and add entries to the `allow` or `deny` arrays:

```json
{
  "name": "Rule Name",
  "tools": ["Bash"],
  "pattern": "^regex-pattern",
  "reason": "Human-readable reason"
}
```

## Testing

Test the classifier directly:

```bash
echo '{"tool_name": "Bash", "tool_input": {"command": "your-command"}, "cwd": "/your/dir"}' | python classifier.py
```

- Empty stdout = allowed
- JSON in stdout = denied (check `hookSpecificOutput.permissionDecision`)

## Pull Requests

1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Test with Claude Code
5. Submit a PR

## Rule Guidelines

- **Allow rules** should be specific (exact tool names, narrow patterns)
- **Deny rules** should err on the side of safety
- Document the `reason` field clearly — it's shown to the model
- Test both positive and negative cases
