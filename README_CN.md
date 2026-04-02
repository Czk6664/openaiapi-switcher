# OpenAI API Switcher

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-informational.svg)](https://www.microsoft.com/windows)
[![UI](https://img.shields.io/badge/UI-Tkinter-success.svg)](https://docs.python.org/3/library/tkinter.html)

> AI 生成项目声明：本项目由 AI 协助生成并持续迭代完善。

> 默认文档语言：中文（即 `README.md`） | English Docs: [README_EN.md](README_EN.md)

一个面向桌面的 OpenAI 兼容配置切换工具。

## 目录

- [项目价值](#项目价值)
- [核心功能](#核心功能)
- [支持的配置路径](#支持的配置路径)
- [快速开始](#快速开始)
- [目录结构](#目录结构)
- [安全说明](#安全说明)
- [打包产物](#打包产物)

本工具用于统一管理以下客户端的 URL 与 API Key 配置：

- OpenCode
- Codex
- Claude Code

你可以对每个客户端分别设置，并将配置写回到对应文件。

## 项目价值

当你同时使用多个代码助手时，手动改配置容易出错、切换成本高。
本项目提供一套 GUI + CLI，让三类客户端的配置切换在一个工具里完成。

## 核心功能

- 单一 GUI，分标签管理 OpenCode / Codex / Claude Code
- 默认中文界面，支持切换到英文界面
- 自动识别本机配置文件路径并读取当前值
- 分客户端导入 `base URL` + `api key`
- Claude Code 支持 OpenAI 兼容模式与模型切换
  - `ANTHROPIC_MODEL`
  - `ANTHROPIC_SMALL_FAST_MODEL`
- 安全更新：仅改必要字段，保留其余配置

## 支持的配置路径

| 客户端 | 主要配置文件 |
| --- | --- |
| OpenCode | `~/.config/opencode.jsonc`, `~/.config/opencode/opencode.json` |
| Codex | `~/.codex/config.toml`, `~/.codex/auth.json` |
| Claude Code | `~/.claude/settings.json`, `~/.claude/settings.local.json` |

## 快速开始

### 一键启动前端

```powershell
start_frontend.cmd
```

### 启动 GUI

```powershell
python main.py
```

### 扫描当前配置

```powershell
python main.py scan
```

### CLI 导入配置

```powershell
python main.py set --client opencode --url "https://example.com/v1" --api-key "<API_KEY>"
python main.py set --client codex --url "https://example.com/v1" --api-key "<API_KEY>"
python main.py set --client claude --url "https://example.com/v1" --api-key "<API_KEY>" --model "gpt-5.3-codex" --small-model "gpt-5.3-mini"
```

### 自定义 home 目录

```powershell
python main.py --home "C:\Users\23707" scan
```

## 目录结构

- `main.py`：GUI/CLI 统一入口
- `switcher/config_manager.py`：扫描、读取、写入逻辑
- `switcher/gui.py`：Tkinter 图形界面（默认中文，可切换英文）
- `launch_gui.cmd`：一键启动脚本
- `start_frontend.cmd`：一键前端启动脚本（优先使用 EXE）

## 安全说明

- 仓库中不包含任何真实 API Key。
- 不会自动把你本机配置文件提交到版本库。
- 请确保 `.codex/auth.json`、`.claude/settings.json`、`.config/opencode*.json*` 不进入 Git。
- 项目已配置 `.gitignore` 防止常见本地文件泄漏。

## 打包产物

- ZIP：`dist/config-switcher.zip`
- EXE：`dist/openaiapi-switcher.exe`
- 便携包：`dist/openaiapi-switcher-portable.zip`

以上产物仅包含项目程序，不包含你本地的个人配置文件。
