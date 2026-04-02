from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from .config_manager import ClientState, ConfigManager, mask_secret


LANGUAGE_LABELS = {
    "中文": "zh",
    "English": "en",
}

CLIENTS = ("opencode", "codex", "claude")

I18N = {
    "zh": {
        "window_title": "OpenAI 配置切换器",
        "header_title": "OpenAI 兼容配置切换器",
        "header_subtitle": "统一管理 OpenCode / Codex / Claude Code 的 URL 与 API Key",
        "language_label": "界面语言:",
        "reload_all": "全部刷新",
        "home_prefix": "主目录: ",
        "current_group": "当前检测",
        "edit_group": "导入与更新",
        "status_prefix": "状态: ",
        "status_installed": "已安装",
        "status_missing": "未检测到",
        "file_exists": "存在",
        "file_missing": "缺失",
        "notes_empty": "无",
        "detected_files": "检测到的文件:",
        "active_file": "当前使用文件:",
        "notes": "备注:",
        "base_url": "Base URL:",
        "api_key": "API Key:",
        "model": "OpenAI 模型:",
        "small_model": "快速模型:",
        "load_current": "加载当前",
        "import_values": "导入 URL + Key",
        "tab_opencode": "OpenCode",
        "tab_codex": "Codex",
        "tab_claude": "Claude Code",
        "missing_title": "缺少输入",
        "missing_body": "URL 和 API Key 不能为空。",
        "success_title": "导入成功",
        "failed_title": "更新失败",
        "msg_opencode": "OpenCode 已更新: {path}\nAPI Key: {key}",
        "msg_codex": "Codex 已更新:\n{config}\n{auth}\nAPI Key: {key}",
        "msg_claude": "Claude Code 已更新: {path}\n模型: {model}\n快速模型: {small}\nAPI Key: {key}",
        "unchanged": "(未修改)",
    },
    "en": {
        "window_title": "OpenAI Config Switcher",
        "header_title": "OpenAI-Compatible Config Switcher",
        "header_subtitle": "Manage URL and API key for OpenCode / Codex / Claude Code in one place",
        "language_label": "Language:",
        "reload_all": "Reload All",
        "home_prefix": "Home: ",
        "current_group": "Current Detection",
        "edit_group": "Import and Update",
        "status_prefix": "Status: ",
        "status_installed": "Installed",
        "status_missing": "Not detected",
        "file_exists": "exists",
        "file_missing": "missing",
        "notes_empty": "-",
        "detected_files": "Detected files:",
        "active_file": "Active file:",
        "notes": "Notes:",
        "base_url": "Base URL:",
        "api_key": "API Key:",
        "model": "OpenAI Model:",
        "small_model": "Small Model:",
        "load_current": "Load Current",
        "import_values": "Import URL + Key",
        "tab_opencode": "OpenCode",
        "tab_codex": "Codex",
        "tab_claude": "Claude Code",
        "missing_title": "Missing Value",
        "missing_body": "Both URL and API key are required.",
        "success_title": "Import complete",
        "failed_title": "Update failed",
        "msg_opencode": "OpenCode updated: {path}\nAPI key: {key}",
        "msg_codex": "Codex updated:\n{config}\n{auth}\nAPI key: {key}",
        "msg_claude": "Claude Code updated: {path}\nModel: {model}\nSmall model: {small}\nAPI key: {key}",
        "unchanged": "(unchanged)",
    },
}


class SwitcherApp(tk.Tk):
    def __init__(self, manager: ConfigManager) -> None:
        super().__init__()
        self.manager = manager
        self.language = "zh"
        self.title(I18N[self.language]["window_title"])
        self.geometry("980x660")
        self.minsize(900, 580)

        self._widgets: dict[str, dict[str, tk.StringVar]] = {}
        self._ui: dict[str, dict[str, ttk.Widget]] = {}
        self._state_cache: dict[str, ClientState] = {}

        self._header_title_var = tk.StringVar(value="")
        self._header_subtitle_var = tk.StringVar(value="")
        self._home_var = tk.StringVar(value="")
        self._language_var = tk.StringVar(value="中文")

        self._build_ui()
        self._apply_language()
        self.reload_all()

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill=tk.BOTH, expand=True)

        top_bar = ttk.Frame(root)
        top_bar.pack(fill=tk.X, pady=(0, 8))

        title_block = ttk.Frame(top_bar)
        title_block.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(title_block, textvariable=self._header_title_var).pack(anchor="w")
        ttk.Label(title_block, textvariable=self._header_subtitle_var).pack(anchor="w", pady=(2, 0))

        actions = ttk.Frame(top_bar)
        actions.pack(side=tk.RIGHT)
        self._language_label = ttk.Label(actions, text="")
        self._language_label.pack(side=tk.LEFT, padx=(0, 6))

        self._language_combo = ttk.Combobox(
            actions,
            state="readonly",
            width=8,
            textvariable=self._language_var,
            values=tuple(LANGUAGE_LABELS.keys()),
        )
        self._language_combo.pack(side=tk.LEFT, padx=(0, 8))
        self._language_combo.bind("<<ComboboxSelected>>", self._on_language_changed)

        self._reload_button = ttk.Button(actions, text="", command=self.reload_all)
        self._reload_button.pack(side=tk.LEFT)

        ttk.Label(root, textvariable=self._home_var).pack(fill=tk.X, anchor="w", pady=(0, 8))
        ttk.Separator(root).pack(fill=tk.X, pady=(0, 10))

        self._notebook = ttk.Notebook(root)
        self._notebook.pack(fill=tk.BOTH, expand=True)

        for client in CLIENTS:
            frame = ttk.Frame(self._notebook, padding=12)
            self._notebook.add(frame, text=self._tab_title(client))
            self._build_client_tab(frame, client)

    def _build_client_tab(self, frame: ttk.Frame, client: str) -> None:
        vars_map = {
            "status": tk.StringVar(value=""),
            "files": tk.StringVar(value=""),
            "active": tk.StringVar(value=""),
            "notes": tk.StringVar(value=""),
            "url": tk.StringVar(value=""),
            "key": tk.StringVar(value=""),
            "model": tk.StringVar(value=""),
            "small_model": tk.StringVar(value=""),
        }
        self._widgets[client] = vars_map

        ui: dict[str, ttk.Widget] = {}
        self._ui[client] = ui

        current_group = ttk.LabelFrame(frame, padding=10)
        current_group.pack(fill=tk.X, pady=(0, 12))
        ui["current_group"] = current_group

        row = 0
        ttk.Label(current_group, textvariable=vars_map["status"]).grid(row=row, column=0, columnspan=2, sticky="w")
        row += 1

        detected_caption = ttk.Label(current_group, text="")
        detected_caption.grid(row=row, column=0, sticky="nw", pady=(8, 0), padx=(0, 8))
        ttk.Label(current_group, textvariable=vars_map["files"], wraplength=760, justify=tk.LEFT).grid(
            row=row, column=1, sticky="w", pady=(8, 0)
        )
        ui["detected_caption"] = detected_caption
        row += 1

        active_caption = ttk.Label(current_group, text="")
        active_caption.grid(row=row, column=0, sticky="nw", pady=(4, 0), padx=(0, 8))
        ttk.Label(current_group, textvariable=vars_map["active"], wraplength=760, justify=tk.LEFT).grid(
            row=row, column=1, sticky="w", pady=(4, 0)
        )
        ui["active_caption"] = active_caption
        row += 1

        notes_caption = ttk.Label(current_group, text="")
        notes_caption.grid(row=row, column=0, sticky="nw", pady=(4, 0), padx=(0, 8))
        ttk.Label(current_group, textvariable=vars_map["notes"], wraplength=760, justify=tk.LEFT).grid(
            row=row, column=1, sticky="w", pady=(4, 0)
        )
        ui["notes_caption"] = notes_caption

        current_group.columnconfigure(1, weight=1)

        edit_group = ttk.LabelFrame(frame, padding=10)
        edit_group.pack(fill=tk.X)
        ui["edit_group"] = edit_group

        row = 0
        url_caption = ttk.Label(edit_group, text="")
        url_caption.grid(row=row, column=0, sticky="e", padx=(0, 8), pady=4)
        ttk.Entry(edit_group, textvariable=vars_map["url"], width=90).grid(row=row, column=1, sticky="ew", pady=4)
        ui["url_caption"] = url_caption
        row += 1

        key_caption = ttk.Label(edit_group, text="")
        key_caption.grid(row=row, column=0, sticky="e", padx=(0, 8), pady=4)
        ttk.Entry(edit_group, textvariable=vars_map["key"], width=90, show="*").grid(row=row, column=1, sticky="ew", pady=4)
        ui["key_caption"] = key_caption
        row += 1

        if client == "claude":
            model_caption = ttk.Label(edit_group, text="")
            model_caption.grid(row=row, column=0, sticky="e", padx=(0, 8), pady=4)
            ttk.Entry(edit_group, textvariable=vars_map["model"], width=90).grid(row=row, column=1, sticky="ew", pady=4)
            ui["model_caption"] = model_caption
            row += 1

            small_model_caption = ttk.Label(edit_group, text="")
            small_model_caption.grid(row=row, column=0, sticky="e", padx=(0, 8), pady=4)
            ttk.Entry(edit_group, textvariable=vars_map["small_model"], width=90).grid(
                row=row,
                column=1,
                sticky="ew",
                pady=4,
            )
            ui["small_model_caption"] = small_model_caption
            row += 1

        button_row = ttk.Frame(edit_group)
        button_row.grid(row=row, column=0, columnspan=2, sticky="w", pady=(10, 0))

        load_button = ttk.Button(button_row, text="", command=lambda c=client: self.reload_client(c))
        load_button.pack(side=tk.LEFT)
        import_button = ttk.Button(button_row, text="", command=lambda c=client: self.save_client(c))
        import_button.pack(side=tk.LEFT, padx=(10, 0))
        ui["load_button"] = load_button
        ui["import_button"] = import_button

        edit_group.columnconfigure(1, weight=1)

    def _tab_title(self, client: str) -> str:
        t = self._t()
        if client == "opencode":
            return t["tab_opencode"]
        if client == "codex":
            return t["tab_codex"]
        return t["tab_claude"]

    def _t(self) -> dict[str, str]:
        return I18N[self.language]

    def _on_language_changed(self, _event: tk.Event) -> None:
        selected = self._language_var.get()
        self.language = LANGUAGE_LABELS.get(selected, "zh")
        self._apply_language()

    def _apply_language(self) -> None:
        t = self._t()

        self.title(t["window_title"])
        self._header_title_var.set(t["header_title"])
        self._header_subtitle_var.set(t["header_subtitle"])
        self._home_var.set(f"{t['home_prefix']}{self.manager.home}")

        self._language_label.configure(text=t["language_label"])
        self._reload_button.configure(text=t["reload_all"])

        for index, client in enumerate(CLIENTS):
            self._notebook.tab(index, text=self._tab_title(client))
            ui = self._ui[client]

            ui["current_group"].configure(text=t["current_group"])
            ui["edit_group"].configure(text=t["edit_group"])
            ui["detected_caption"].configure(text=t["detected_files"])
            ui["active_caption"].configure(text=t["active_file"])
            ui["notes_caption"].configure(text=t["notes"])
            ui["url_caption"].configure(text=t["base_url"])
            ui["key_caption"].configure(text=t["api_key"])
            ui["load_button"].configure(text=t["load_current"])
            ui["import_button"].configure(text=t["import_values"])

            if client == "claude":
                ui["model_caption"].configure(text=t["model"])
                ui["small_model_caption"].configure(text=t["small_model"])

        for client, state in self._state_cache.items():
            self._apply_state(client, state)

    def reload_all(self) -> None:
        for client in CLIENTS:
            self.reload_client(client)

    def reload_client(self, client: str) -> None:
        if client == "opencode":
            state = self.manager.scan_opencode()
        elif client == "codex":
            state = self.manager.scan_codex()
        else:
            state = self.manager.scan_claude()

        self._apply_state(client, state)

    def _apply_state(self, client: str, state: ClientState) -> None:
        self._state_cache[client] = state
        t = self._t()
        vars_map = self._widgets[client]
        status = t["status_installed"] if state.installed else t["status_missing"]
        vars_map["status"].set(f"{t['status_prefix']}{status}")

        files_text = " | ".join(
            [f"{path} ({t['file_exists'] if path.exists() else t['file_missing']})" for path in state.files]
        )
        vars_map["files"].set(files_text)
        vars_map["active"].set(str(state.selected_file))

        notes = "; ".join(state.notes) if state.notes else t["notes_empty"]
        vars_map["notes"].set(notes)

        vars_map["url"].set(state.url)
        vars_map["key"].set(state.api_key)
        vars_map["model"].set(state.model)
        vars_map["small_model"].set(state.small_model)

    def save_client(self, client: str) -> None:
        t = self._t()
        vars_map = self._widgets[client]
        url = vars_map["url"].get().strip()
        api_key = vars_map["key"].get().strip()

        if not url or not api_key:
            messagebox.showerror(t["missing_title"], t["missing_body"])
            return

        try:
            if client == "opencode":
                target = self.manager.update_opencode(url=url, api_key=api_key)
                message = t["msg_opencode"].format(path=target, key=mask_secret(api_key))
            elif client == "codex":
                config_path, auth_path = self.manager.update_codex(url=url, api_key=api_key)
                message = t["msg_codex"].format(config=config_path, auth=auth_path, key=mask_secret(api_key))
            else:
                model = vars_map["model"].get().strip()
                small_model = vars_map["small_model"].get().strip()
                target = self.manager.update_claude(
                    url=url,
                    api_key=api_key,
                    model=model,
                    small_model=small_model,
                )
                message = t["msg_claude"].format(
                    path=target,
                    model=model or t["unchanged"],
                    small=small_model or t["unchanged"],
                    key=mask_secret(api_key),
                )

            self.reload_client(client)
            messagebox.showinfo(t["success_title"], message)
        except Exception as exc:
            messagebox.showerror(t["failed_title"], str(exc))
