# Claude Auto Mode Bridge

<div align="center">

[English](README_EN.md) | [中文](README.md)

**让 Claude Code 的 auto mode 支持任意模型 — MiMo、DeepSeek、OpenRouter 等**

</div>

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-compatible-brightgreen)](https://docs.anthropic.com/en/docs/claude-code)
[![GitHub Stars](https://img.shields.io/github/stars/wcz234/claude-auto-mode-bridge?style=social)](https://github.com/wcz234/claude-auto-mode-bridge)

> Claude Code 的 auto mode 依赖 Anthropic 服务端的 AI 分类器，换用其他模型后就失效了。本项目通过本地规则引擎 + LLM 兜底，让 auto mode 在任意 Anthropic 兼容后端上都能正常工作。

```
之前:  claude --permission-mode auto  →  只支持 Claude 模型
之后:  claude                         →  任意模型都能用 auto mode
```

---

## 为什么需要这个

[Claude Code](https://docs.anthropic.com/en/docs/claude-code) 是最强的自主编程 Agent。通过 [deepclaude](https://github.com/aattaran/deepclaude) 等工具可以替换后端模型（DeepSeek、MiMo、OpenRouter），但 `--permission-mode auto` **会失效**，因为它依赖 Anthropic 的服务端 AI 分类器。

**本项目用本地 hook 替代了这个分类器**，适配任意后端。

| | Anthropic Claude | MiMo / DeepSeek / OpenRouter |
|---|---|---|
| 工具循环 | 正常 | 正常（通过代理） |
| 文件编辑 | 正常 | 正常 |
| `--permission-mode auto` | 正常 | 失效 |
| **使用本项目后** | 正常 | 正常 |

---

## 快速开始（30 秒）

```bash
# 1. 克隆
git clone https://github.com/wcz234/claude-auto-mode-bridge.git
cd claude-auto-mode-bridge

# 2. 安装
python install.py

# 3. 正常使用 Claude Code，auto mode 已生效
claude
```

安装脚本会自动在 `~/.claude/settings.json` 中注册 hook，无需手动配置。

---

## 工作原理

```
Claude Code（任意模型后端）
  │
  ├── 工具调用（Bash / Edit / Write / ...）
  │     ↓
  ├── PreToolUse Hook  ←  本项目
  │     │
  │     ├── 第 1 层：规则引擎（<1ms）
  │     │     ├── 匹配到 deny 规则  → 立即拦截
  │     │     └── 匹配到 allow 规则 → 立即放行
  │     │
  │     └── 第 2 层：LLM 兜底（可选，~1s）
  │           └── 无规则匹配  → 询问模型决策
  │
  └── 工具执行（或被拦截）
```

**deny 规则优先检查**（安全优先），其次是 allow 规则。如果都没有命中，则由 LLM 兜底分类。

---

## 内置规则

### 拦截（仅破坏性删除操作）

| 类别 | 示例 |
|------|------|
| 危险递归删除 | `rm -rf /` |
| 系统级破坏 | `sudo rm`、`mkfs`、`dd if=` |
| 危险 Git 重置 | `git reset --hard`、`git clean -f` |
| 敏感目录删除 | `rm -rf ~/.ssh`、`rm -rf ~/.aws` |

### 放行（其他所有操作）

宽松模式下，以下操作默认全部放行：
- Git force push、push 到 main
- 任意文件读写
- 包安装、构建、测试
- curl/管道操作
- 生产部署

---

## LLM 兜底

对于规则未覆盖的操作，可以调用你的模型来分类。复用 `settings.json` 中已配置的 API 凭证。

```json
// rules.json
"llm_fallback": {
  "enabled": true,
  "timeout_seconds": 10
}
```

兜底使用你配置的最便宜的模型（Haiku 级别），以最小化成本和延迟。如果 API 调用失败，默认**放行**（fail-open）。

---

## 支持的后端

| 后端 | 配置方式 |
|------|----------|
| **MiMo（小米）** | 设置 `ANTHROPIC_BASE_URL` 为 MiMo 代理地址 |
| **DeepSeek** | 设置 `ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN` |
| **OpenRouter** | 设置 `ANTHROPIC_BASE_URL` 为 OpenRouter 端点 |
| **Fireworks AI** | 设置 `ANTHROPIC_BASE_URL` 为 Fireworks 端点 |
| **任意 Anthropic 兼容** | 只要支持 `/v1/messages` 接口即可 |

MiMo 配置示例（`settings.json`）：
```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://your-proxy.com/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "your-api-key",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "your-model",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "your-model",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "your-model"
  }
}
```

更多后端配置示例见 [examples/deepseek-config.md](examples/deepseek-config.md)。

---

## 自定义规则

### 添加自定义规则

编辑 `~/.claude/auto-mode-bridge/rules.json`：

```json
{
  "name": "允许我的部署命令",
  "tools": ["Bash"],
  "pattern": "^my-deploy --staging",
  "reason": "预发布环境部署是安全的"
}
```

### 禁用 LLM 兜底

```json
"llm_fallback": {
  "enabled": false
}
```

### 规则字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | 规则名称，用于日志 |
| `tools` | string[] | 适用的工具列表 |
| `pattern` | string | 正则表达式（匹配 Bash 命令） |
| `path_check` | string | 路径条件：`in_project`、`is_system_path`、`is_package_dir`、`in_memory_dir`、`is_agent_config` |
| `reason` | string | 人类可读的原因说明 |
| `allow_if_contains` | string[] | 额外的放行条件（仅用于 allow 规则） |

更多自定义规则示例见 [examples/custom-rules.md](examples/custom-rules.md)。

---

## 卸载

```bash
python uninstall.py
```

或手动删除 `~/.claude/settings.json` 中的 `hooks` 部分。

---

## 常见问题

**Q: Claude（Anthropic）模型也能用吗？**
A: 可以。它会在 Anthropic 自己的分类器之前增加一层本地预检，两层互不冲突。

**Q: 会影响工作效率吗？**
A: 规则检查 <1ms。LLM 兜底仅在模糊场景触发，约 1s。绝大多数工具调用会立即命中 allow/deny 规则。

**Q: LLM 兜底判断错了怎么办？**
A: 默认 fail-open（失败放行）。可以完全禁用（`"enabled": false`），纯靠规则。

**Q: 能和 [deepclaude](https://github.com/aattaran/deepclaude) 一起用吗？**
A: 可以。先安装 deepclaude 设置代理，再安装本项目启用 auto mode。

**Q: 支持 Windows 吗？**
A: 支持。分类器同时处理 `/` 和 `\` 路径分隔符。

---

## 贡献

欢迎贡献！详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## 许可证

[MIT](LICENSE) - 可自由用于个人和商业项目。

---

## 致谢

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) by Anthropic
- [deepclaude](https://github.com/aattaran/deepclaude) 的多后端代理模式
- [hookify](https://github.com/anthropics/claude-code/tree/main/plugins/hookify) 的 hook 规则引擎模式

---

<div align="center">

如果这个项目对你有帮助，请点个 Star 支持一下

</div>
