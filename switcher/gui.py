from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from .config_manager import ClientState, ConfigManager, mask_secret


class SwitcherApp(tk.Tk):
    def __init__(self, manager: ConfigManager) -> None:
        super().__init__()
        self.manager = manager
        self.title("OpenAI-Compatible Config Switcher")
        self.geometry("960x620")

        self._widgets: dict[str, dict[str, tk.StringVar]] = {}
        self._build_ui()
        self.reload_all()

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill=tk.BOTH, expand=True)

        top_bar = ttk.Frame(root)
        top_bar.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(top_bar, text=f"Home: {self.manager.home}").pack(side=tk.LEFT)
        ttk.Button(top_bar, text="Reload All", command=self.reload_all).pack(side=tk.RIGHT)

        notebook = ttk.Notebook(root)
        notebook.pack(fill=tk.BOTH, expand=True)

        for client in ("opencode", "codex", "claude"):
            frame = ttk.Frame(notebook, padding=12)
            notebook.add(frame, text=self._tab_title(client))
            self._build_client_tab(frame, client)

    def _build_client_tab(self, frame: ttk.Frame, client: str) -> None:
        vars_map = {
            "status": tk.StringVar(value="Scanning..."),
            "files": tk.StringVar(value=""),
            "active": tk.StringVar(value=""),
            "notes": tk.StringVar(value=""),
            "url": tk.StringVar(value=""),
            "key": tk.StringVar(value=""),
            "model": tk.StringVar(value=""),
            "small_model": tk.StringVar(value=""),
        }
        self._widgets[client] = vars_map

        row = 0
        ttk.Label(frame, textvariable=vars_map["status"]).grid(row=row, column=0, columnspan=3, sticky="w")
        row += 1

        ttk.Label(frame, text="Detected files:").grid(row=row, column=0, sticky="nw", pady=(8, 0))
        ttk.Label(frame, textvariable=vars_map["files"], wraplength=760).grid(
            row=row, column=1, columnspan=2, sticky="w", pady=(8, 0)
        )
        row += 1

        ttk.Label(frame, text="Active file:").grid(row=row, column=0, sticky="w", pady=(4, 0))
        ttk.Label(frame, textvariable=vars_map["active"], wraplength=760).grid(
            row=row, column=1, columnspan=2, sticky="w", pady=(4, 0)
        )
        row += 1

        ttk.Label(frame, text="Notes:").grid(row=row, column=0, sticky="w", pady=(4, 0))
        ttk.Label(frame, textvariable=vars_map["notes"], wraplength=760).grid(
            row=row, column=1, columnspan=2, sticky="w", pady=(4, 0)
        )
        row += 1

        ttk.Separator(frame).grid(row=row, column=0, columnspan=3, sticky="ew", pady=10)
        row += 1

        ttk.Label(frame, text="Base URL:").grid(row=row, column=0, sticky="e", padx=(0, 8), pady=4)
        ttk.Entry(frame, textvariable=vars_map["url"], width=84).grid(row=row, column=1, columnspan=2, sticky="ew", pady=4)
        row += 1

        ttk.Label(frame, text="API Key:").grid(row=row, column=0, sticky="e", padx=(0, 8), pady=4)
        ttk.Entry(frame, textvariable=vars_map["key"], width=84, show="*").grid(row=row, column=1, columnspan=2, sticky="ew", pady=4)
        row += 1

        if client == "claude":
            ttk.Label(frame, text="OpenAI Model:").grid(row=row, column=0, sticky="e", padx=(0, 8), pady=4)
            ttk.Entry(frame, textvariable=vars_map["model"], width=84).grid(
                row=row, column=1, columnspan=2, sticky="ew", pady=4
            )
            row += 1

            ttk.Label(frame, text="Small Model:").grid(row=row, column=0, sticky="e", padx=(0, 8), pady=4)
            ttk.Entry(frame, textvariable=vars_map["small_model"], width=84).grid(
                row=row, column=1, columnspan=2, sticky="ew", pady=4
            )
            row += 1

        button_row = ttk.Frame(frame)
        button_row.grid(row=row, column=0, columnspan=3, sticky="w", pady=(12, 0))

        ttk.Button(button_row, text="Load Current", command=lambda c=client: self.reload_client(c)).pack(side=tk.LEFT)
        ttk.Button(button_row, text="Import URL + Key", command=lambda c=client: self.save_client(c)).pack(
            side=tk.LEFT, padx=(10, 0)
        )

        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)

    def _tab_title(self, client: str) -> str:
        if client == "opencode":
            return "OpenCode"
        if client == "codex":
            return "Codex"
        return "Claude Code"

    def reload_all(self) -> None:
        for client in ("opencode", "codex", "claude"):
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
        vars_map = self._widgets[client]
        status = "Installed" if state.installed else "Not detected"
        vars_map["status"].set(f"Status: {status}")

        files_text = " | ".join([f"{path} ({'exists' if path.exists() else 'missing'})" for path in state.files])
        vars_map["files"].set(files_text)
        vars_map["active"].set(str(state.selected_file))

        notes = "; ".join(state.notes) if state.notes else "-"
        vars_map["notes"].set(notes)

        vars_map["url"].set(state.url)
        vars_map["key"].set(state.api_key)
        vars_map["model"].set(state.model)
        vars_map["small_model"].set(state.small_model)

    def save_client(self, client: str) -> None:
        vars_map = self._widgets[client]
        url = vars_map["url"].get().strip()
        api_key = vars_map["key"].get().strip()

        if not url or not api_key:
            messagebox.showerror("Missing value", "Both URL and API key are required.")
            return

        try:
            if client == "opencode":
                target = self.manager.update_opencode(url=url, api_key=api_key)
                message = f"OpenCode updated: {target}\nAPI key: {mask_secret(api_key)}"
            elif client == "codex":
                config_path, auth_path = self.manager.update_codex(url=url, api_key=api_key)
                message = (
                    f"Codex updated:\n{config_path}\n{auth_path}\n"
                    f"API key: {mask_secret(api_key)}"
                )
            else:
                model = vars_map["model"].get().strip()
                small_model = vars_map["small_model"].get().strip()
                target = self.manager.update_claude(
                    url=url,
                    api_key=api_key,
                    model=model,
                    small_model=small_model,
                )
                message = (
                    f"Claude Code updated: {target}\n"
                    f"Model: {model or '(unchanged)'}\n"
                    f"Small model: {small_model or '(unchanged)'}\n"
                    f"API key: {mask_secret(api_key)}"
                )

            self.reload_client(client)
            messagebox.showinfo("Import complete", message)
        except Exception as exc:
            messagebox.showerror("Update failed", str(exc))
