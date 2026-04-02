from __future__ import annotations

import argparse
from pathlib import Path

from switcher import ConfigManager, mask_secret
from switcher.gui import SwitcherApp


def print_state(name: str, state) -> None:
    print(f"[{name}]")
    print(f"  installed: {state.installed}")
    print(f"  active file: {state.selected_file}")
    print(f"  detected files:")
    for path in state.files:
        marker = "exists" if path.exists() else "missing"
        print(f"    - {path} ({marker})")
    print(f"  url: {state.url or '-'}")
    print(f"  api_key: {mask_secret(state.api_key) or '-'}")
    if state.model:
        print(f"  model: {state.model}")
    if state.small_model:
        print(f"  small_model: {state.small_model}")
    if state.notes:
        print("  notes:")
        for note in state.notes:
            print(f"    - {note}")
    print()


def run_scan(manager: ConfigManager) -> int:
    states = manager.scan_all()
    for name in ("opencode", "codex", "claude"):
        print_state(name, states[name])
    return 0


def run_set(manager: ConfigManager, args: argparse.Namespace) -> int:
    if args.client == "opencode":
        target = manager.update_opencode(url=args.url, api_key=args.api_key)
        print(f"OpenCode updated: {target}")
    elif args.client == "codex":
        config_path, auth_path = manager.update_codex(url=args.url, api_key=args.api_key)
        print(f"Codex config updated: {config_path}")
        print(f"Codex auth updated: {auth_path}")
    else:
        target = manager.update_claude(
            url=args.url,
            api_key=args.api_key,
            model=args.model,
            small_model=args.small_model,
        )
        print(f"Claude Code updated: {target}")
    print("Done.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="config-switcher",
        description="Detect and import OpenAI-compatible URL/API key for OpenCode, Codex, and Claude Code.",
    )
    parser.add_argument(
        "--home",
        type=Path,
        default=Path.home(),
        help="Home directory that contains .codex/.claude/.config",
    )

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("scan", help="Scan current configuration files")

    set_parser = subparsers.add_parser("set", help="Import URL + API key into one client")
    set_parser.add_argument("--client", choices=["opencode", "codex", "claude"], required=True)
    set_parser.add_argument("--url", required=True, help="OpenAI-compatible base URL")
    set_parser.add_argument("--api-key", required=True, help="API key")
    set_parser.add_argument("--model", default="", help="Claude model (used only for --client claude)")
    set_parser.add_argument(
        "--small-model",
        default="",
        help="Claude small/fast model (used only for --client claude)",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    manager = ConfigManager(home=args.home)

    if args.command == "scan":
        return run_scan(manager)
    if args.command == "set":
        return run_set(manager, args)

    app = SwitcherApp(manager)
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
