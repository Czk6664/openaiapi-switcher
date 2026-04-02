from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ClientState:
    client: str
    installed: bool
    files: list[Path]
    selected_file: Path
    url: str = ""
    api_key: str = ""
    model: str = ""
    small_model: str = ""
    notes: list[str] = field(default_factory=list)


def mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


class ConfigManager:
    def __init__(self, home: Path | None = None) -> None:
        self.home = Path(home) if home else Path.home()

    @property
    def opencode_candidates(self) -> list[Path]:
        return [
            self.home / ".config" / "opencode.jsonc",
            self.home / ".config" / "opencode" / "opencode.json",
        ]

    @property
    def codex_config_path(self) -> Path:
        return self.home / ".codex" / "config.toml"

    @property
    def codex_auth_path(self) -> Path:
        return self.home / ".codex" / "auth.json"

    @property
    def claude_candidates(self) -> list[Path]:
        return [
            self.home / ".claude" / "settings.json",
            self.home / ".claude" / "settings.local.json",
        ]

    def scan_all(self) -> dict[str, ClientState]:
        return {
            "opencode": self.scan_opencode(),
            "codex": self.scan_codex(),
            "claude": self.scan_claude(),
        }

    def scan_opencode(self) -> ClientState:
        files = self.opencode_candidates
        existing = [p for p in files if p.exists()]
        selected = existing[0] if existing else files[0]
        state = ClientState(
            client="opencode",
            installed=bool(existing),
            files=files,
            selected_file=selected,
        )

        if not selected.exists():
            return state

        try:
            data = self._read_jsonc_dict(selected)
        except Exception as exc:
            state.notes.append(f"Cannot parse {selected}: {exc}")
            return state

        provider = data.get("provider")
        if not isinstance(provider, dict):
            state.notes.append("No provider object found in OpenCode config")
            return state

        selected_provider_name = ""
        selected_provider: dict[str, Any] | None = None

        openai_candidate = provider.get("openai")
        if isinstance(openai_candidate, dict):
            selected_provider_name = "openai"
            selected_provider = openai_candidate
        else:
            for name, config in provider.items():
                if not isinstance(config, dict):
                    continue
                options = config.get("options")
                if not isinstance(options, dict):
                    continue
                npm_value = str(config.get("npm", ""))
                if (
                    "openai-compatible" in npm_value
                    or "openai" in name.lower()
                    or "baseURL" in options
                    or "apiKey" in options
                ):
                    selected_provider_name = str(name)
                    selected_provider = config
                    break

        if not selected_provider:
            state.notes.append("No OpenAI-compatible provider found in OpenCode config")
            return state

        options = selected_provider.get("options")
        if isinstance(options, dict):
            state.url = str(options.get("baseURL") or options.get("base_url") or "")
            state.api_key = str(options.get("apiKey") or options.get("api_key") or "")

        if selected_provider_name and selected_provider_name != "openai":
            state.notes.append(f"Detected provider.{selected_provider_name}")

        return state

    def update_opencode(
        self,
        url: str,
        api_key: str,
        file_path: Path | None = None,
    ) -> Path:
        target = file_path or self._first_existing(self.opencode_candidates) or self.opencode_candidates[0]

        data: dict[str, Any]
        if target.exists():
            data = self._read_jsonc_dict(target)
        else:
            data = {}

        provider = data.get("provider")
        if not isinstance(provider, dict):
            provider = {}
            data["provider"] = provider

        openai_cfg = provider.get("openai")
        if not isinstance(openai_cfg, dict):
            openai_cfg = {}
            provider["openai"] = openai_cfg

        if "npm" not in openai_cfg:
            openai_cfg["npm"] = "@ai-sdk/openai-compatible"
        if "name" not in openai_cfg:
            openai_cfg["name"] = "OpenAI"

        options = openai_cfg.get("options")
        if not isinstance(options, dict):
            options = {}
            openai_cfg["options"] = options

        options["baseURL"] = url.strip()
        options["apiKey"] = api_key.strip()

        if "$schema" not in data:
            data["$schema"] = "https://opencode.ai/config.json"

        self._write_json(target, data)
        return target

    def scan_codex(self) -> ClientState:
        config_path = self.codex_config_path
        auth_path = self.codex_auth_path

        state = ClientState(
            client="codex",
            installed=config_path.exists() or auth_path.exists(),
            files=[config_path, auth_path],
            selected_file=config_path,
        )

        if config_path.exists():
            try:
                text = config_path.read_text(encoding="utf-8")
                data = tomllib.loads(text)
                providers = data.get("model_providers")
                if isinstance(providers, dict):
                    openai_provider = providers.get("OpenAI")
                    if isinstance(openai_provider, dict):
                        state.url = str(openai_provider.get("base_url") or "")
                state.model = str(data.get("model") or "")
            except Exception as exc:
                state.notes.append(f"Cannot parse {config_path}: {exc}")

        if auth_path.exists():
            try:
                auth_data = self._read_json_dict(auth_path)
                state.api_key = str(auth_data.get("OPENAI_API_KEY") or "")
            except Exception as exc:
                state.notes.append(f"Cannot parse {auth_path}: {exc}")

        return state

    def update_codex(
        self,
        url: str,
        api_key: str,
        config_path: Path | None = None,
        auth_path: Path | None = None,
    ) -> tuple[Path, Path]:
        target_config = config_path or self.codex_config_path
        target_auth = auth_path or self.codex_auth_path

        if target_config.exists():
            text = target_config.read_text(encoding="utf-8")
        else:
            text = (
                'model_provider = "OpenAI"\n'
                'model = "gpt-5.3-codex"\n\n'
                "[model_providers.OpenAI]\n"
                'name = "OpenAI"\n'
                'wire_api = "responses"\n'
                "requires_openai_auth = true\n"
            )

        text = self._normalize_newlines(text)

        text = self._upsert_toml_top_key(text, "model_provider", "OpenAI")
        text = self._upsert_toml_section_key(text, "model_providers.OpenAI", "name", "OpenAI")
        text = self._upsert_toml_section_key(text, "model_providers.OpenAI", "base_url", url.strip())

        target_config.parent.mkdir(parents=True, exist_ok=True)
        target_config.write_text(text, encoding="utf-8")

        if target_auth.exists():
            auth_data = self._read_json_dict(target_auth)
        else:
            auth_data = {}
        auth_data["OPENAI_API_KEY"] = api_key.strip()

        self._write_json(target_auth, auth_data)
        return target_config, target_auth

    def scan_claude(self) -> ClientState:
        files = self.claude_candidates
        existing = [p for p in files if p.exists()]
        selected = existing[0] if existing else files[0]

        state = ClientState(
            client="claude",
            installed=bool(existing),
            files=files,
            selected_file=selected,
        )

        if not selected.exists():
            return state

        try:
            data = self._read_json_dict(selected)
        except Exception as exc:
            state.notes.append(f"Cannot parse {selected}: {exc}")
            return state

        env = data.get("env")
        if not isinstance(env, dict):
            state.notes.append("No env object found in Claude settings")
            return state

        state.url = str(env.get("ANTHROPIC_BASE_URL") or "")
        state.api_key = str(env.get("ANTHROPIC_API_KEY") or "")
        state.model = str(env.get("ANTHROPIC_MODEL") or "")
        state.small_model = str(env.get("ANTHROPIC_SMALL_FAST_MODEL") or "")

        compat_flag = str(env.get("CLAUDE_CODE_USE_OPENAI_COMPAT") or "")
        if compat_flag != "1":
            state.notes.append("CLAUDE_CODE_USE_OPENAI_COMPAT is not enabled")

        return state

    def update_claude(
        self,
        url: str,
        api_key: str,
        model: str | None = None,
        small_model: str | None = None,
        file_path: Path | None = None,
    ) -> Path:
        target = file_path or self._first_existing(self.claude_candidates) or self.claude_candidates[0]

        if target.exists():
            data = self._read_json_dict(target)
        else:
            data = {}

        env = data.get("env")
        if not isinstance(env, dict):
            env = {}
            data["env"] = env

        env["ANTHROPIC_BASE_URL"] = url.strip()
        env["ANTHROPIC_API_KEY"] = api_key.strip()
        env["CLAUDE_CODE_USE_OPENAI_COMPAT"] = "1"

        if model is not None and model.strip():
            env["ANTHROPIC_MODEL"] = model.strip()
        if small_model is not None and small_model.strip():
            env["ANTHROPIC_SMALL_FAST_MODEL"] = small_model.strip()

        self._write_json(target, data)
        return target

    def _first_existing(self, paths: list[Path]) -> Path | None:
        for path in paths:
            if path.exists():
                return path
        return None

    def _read_json_dict(self, path: Path) -> dict[str, Any]:
        text = path.read_text(encoding="utf-8-sig")
        data = json.loads(text) if text.strip() else {}
        if not isinstance(data, dict):
            raise ValueError("JSON root is not an object")
        return data

    def _read_jsonc_dict(self, path: Path) -> dict[str, Any]:
        text = path.read_text(encoding="utf-8-sig")
        cleaned = self._strip_jsonc_comments(text)
        cleaned = re.sub(r",(\s*[}\]])", r"\1", cleaned)
        data = json.loads(cleaned) if cleaned.strip() else {}
        if not isinstance(data, dict):
            raise ValueError("JSONC root is not an object")
        return data

    def _write_json(self, path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def _strip_jsonc_comments(self, text: str) -> str:
        result: list[str] = []
        i = 0
        in_string = False
        quote_char = ""
        escaped = False

        while i < len(text):
            ch = text[i]

            if in_string:
                result.append(ch)
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == quote_char:
                    in_string = False
                i += 1
                continue

            if ch in ('"', "'"):
                in_string = True
                quote_char = ch
                result.append(ch)
                i += 1
                continue

            if ch == "/" and i + 1 < len(text):
                next_ch = text[i + 1]
                if next_ch == "/":
                    i += 2
                    while i < len(text) and text[i] != "\n":
                        i += 1
                    continue
                if next_ch == "*":
                    i += 2
                    while i + 1 < len(text) and not (text[i] == "*" and text[i + 1] == "/"):
                        i += 1
                    i += 2
                    continue

            result.append(ch)
            i += 1

        return "".join(result)

    def _upsert_toml_top_key(self, text: str, key: str, value: str | bool | int) -> str:
        value_repr = self._toml_repr(value)
        line_pattern = re.compile(rf"(?m)^[ \t]*{re.escape(key)}[ \t]*=[^\n\r]*$")
        if line_pattern.search(text):
            return line_pattern.sub(f"{key} = {value_repr}", text, count=1)

        first_section = re.search(r"(?m)^\[[^\n\r]+\][ \t]*$", text)
        insertion = f"{key} = {value_repr}\n"

        if first_section:
            return text[: first_section.start()] + insertion + text[first_section.start() :]
        if text and not text.endswith("\n"):
            text += "\n"
        return text + insertion

    def _upsert_toml_section_key(self, text: str, section: str, key: str, value: str | bool | int) -> str:
        header_pattern = re.compile(rf"(?m)^\[{re.escape(section)}\][ \t]*$")
        match = header_pattern.search(text)
        line = f"{key} = {self._toml_repr(value)}"

        if not match:
            if text and not text.endswith("\n"):
                text += "\n"
            return text + f"\n[{section}]\n{line}\n"

        block_start = match.end()
        next_header = re.search(r"(?m)^\[[^\n\r]+\][ \t]*$", text[block_start:])
        block_end = block_start + next_header.start() if next_header else len(text)
        block = text[block_start:block_end]

        key_pattern = re.compile(rf"(?m)^[ \t]*{re.escape(key)}[ \t]*=[^\n\r]*$")
        if key_pattern.search(block):
            new_block = key_pattern.sub(line, block, count=1)
        else:
            if block and not block.endswith("\n"):
                block += "\n"
            new_block = block + line + "\n"

        return text[:block_start] + new_block + text[block_end:]

    def _normalize_newlines(self, text: str) -> str:
        return text.replace("\r\n", "\n").replace("\r", "\n")

    def _toml_repr(self, value: str | bool | int) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, int):
            return str(value)
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
