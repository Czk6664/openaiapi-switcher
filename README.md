# Config Switcher

A local tool for managing OpenAI-compatible URL/API key settings for:

- OpenCode
- Codex
- Claude Code

It can detect config files under your home directory (default: `C:\Users\23707`) and import new values into each client independently.

## Features

- Auto-detects common config file locations for OpenCode, Codex, and Claude Code
- Reads current OpenAI-compatible `base URL` and `API key`
- Imports URL + API key to each client separately
- Supports Claude Code OpenAI-compat mode and model switching
  - `ANTHROPIC_MODEL`
  - `ANTHROPIC_SMALL_FAST_MODEL`

## Project Structure

- `main.py` - CLI entry point and GUI launcher
- `switcher/config_manager.py` - scan/update logic for all clients
- `switcher/gui.py` - Tkinter desktop UI

## Run

From this folder:

```powershell
python main.py
```

This opens a GUI with 3 tabs (`OpenCode`, `Codex`, `Claude Code`).

## CLI Usage

Scan all configs:

```powershell
python main.py scan
```

Import URL + API key for one client:

```powershell
python main.py set --client opencode --url "https://example.com/v1" --api-key "sk-xxx"
python main.py set --client codex --url "https://example.com/v1" --api-key "sk-xxx"
python main.py set --client claude --url "https://example.com/v1" --api-key "sk-xxx" --model "gpt-5.3-codex" --small-model "gpt-5.3-mini"
```

Optional custom home path:

```powershell
python main.py --home "C:\Users\23707" scan
```

## Notes

- The tool preserves unrelated fields in JSON configs and only updates required keys.
- Codex API key is written to `~/.codex/auth.json` as `OPENAI_API_KEY`.
- Claude OpenAI-compat mode is enabled by setting `CLAUDE_CODE_USE_OPENAI_COMPAT = "1"`.

## Security

- This repository does not include your local client config files under `C:\Users\23707`.
- Do not commit files such as `.codex/auth.json`, `.claude/settings.json`, or `.config/opencode*.json*`.
