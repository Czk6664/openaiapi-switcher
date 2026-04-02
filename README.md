# OpenAI API Switcher

A desktop-first config manager for OpenAI-compatible endpoints.

This tool detects and updates local settings for:

- OpenCode
- Codex
- Claude Code

It lets you set each client independently, then writes values back to the correct config file.

## Why This Project

When you use multiple coding assistants, switching provider URL and key by hand is slow and error-prone.
This project provides one GUI and one CLI to manage all three clients from one place.

## Highlights

- One unified GUI with separate tabs for OpenCode, Codex, and Claude Code
- Auto-detect current config paths and active values
- Import `base URL` + `api key` per client independently
- Claude Code OpenAI-compat support with model switching
  - `ANTHROPIC_MODEL`
  - `ANTHROPIC_SMALL_FAST_MODEL`
- Safe writes: preserve unrelated fields and only update required keys

## Supported Config Paths

| Client | Primary files |
| --- | --- |
| OpenCode | `~/.config/opencode.jsonc`, `~/.config/opencode/opencode.json` |
| Codex | `~/.codex/config.toml`, `~/.codex/auth.json` |
| Claude Code | `~/.claude/settings.json`, `~/.claude/settings.local.json` |

## Quick Start

### GUI

```powershell
python main.py
```

### CLI Scan

```powershell
python main.py scan
```

### CLI Import

```powershell
python main.py set --client opencode --url "https://example.com/v1" --api-key "<API_KEY>"
python main.py set --client codex --url "https://example.com/v1" --api-key "<API_KEY>"
python main.py set --client claude --url "https://example.com/v1" --api-key "<API_KEY>" --model "gpt-5.3-codex" --small-model "gpt-5.3-mini"
```

### Optional Home Override

```powershell
python main.py --home "C:\Users\23707" scan
```

## Project Layout

- `main.py` - app entry (GUI + CLI)
- `switcher/config_manager.py` - detect/read/update logic
- `switcher/gui.py` - Tkinter UI
- `launch_gui.cmd` - one-click GUI launcher

## Security Notes

- No real API keys are stored in this repository.
- This project does not include your local client config files.
- Keep files like `.codex/auth.json`, `.claude/settings.json`, and `.config/opencode*.json*` out of version control.
- `.gitignore` is configured to avoid common local artifacts and accidental leakage.

## Packaging

A local zip package is generated at:

- `dist/config-switcher.zip`

This archive contains only project source files, not your personal config files.
