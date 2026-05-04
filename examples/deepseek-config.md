# Using with DeepSeek

## Step 1: Install deepclaude

```bash
# Install deepclaude for the proxy
git clone https://github.com/aattaran/deepclaude.git
cd deepclaude
# Follow deepclaude's setup instructions
```

## Step 2: Install this bridge

```bash
git clone https://github.com/wcz234/claude-auto-mode-bridge.git
cd claude-auto-mode-bridge
python install.py
```

## Step 3: Configure settings.json

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "http://localhost:3200",
    "ANTHROPIC_AUTH_TOKEN": "your-deepseek-api-key",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "deepseek-chat",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "deepseek-chat",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "deepseek-chat"
  }
}
```

## Step 4: Use

```bash
claude
# Auto mode is now active with DeepSeek as the backend
```

---

# Using with MiMo (Xiaomi)

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://your-mimo-proxy.com/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "your-mimo-api-key",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "mimo-v2.5-pro",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "mimo-v2.5-pro",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "mimo-v2.5-pro"
  }
}
```

---

# Using with OpenRouter

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://openrouter.ai/api/v1",
    "ANTHROPIC_AUTH_TOKEN": "your-openrouter-key",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "anthropic/claude-sonnet-4",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "anthropic/claude-sonnet-4",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "anthropic/claude-haiku-4-5-20251001"
  }
}
```
