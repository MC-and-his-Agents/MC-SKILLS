#!/usr/bin/env python3
"""Sync a LoopEngineer plugin snapshot into an MC-SKILLS checkout."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


SNAPSHOT_PATHS = (
    ".codex-plugin",
    "CHANGELOG.md",
    "LICENSE",
    "README.md",
    "README.zh-CN.md",
    "VERSION",
    "docs",
    "mcp",
    "metadata",
    "schemas",
    "scripts",
    "skills",
    "templates",
)

PLUGIN_NAME = "loopengineer"
MARKETPLACE_PATH = Path(".agents/plugins/marketplace.json")


class SyncError(Exception):
    """Raised when the MC-SKILLS sync cannot proceed safely."""


def copy_snapshot(source_root: Path, target_plugin_root: Path) -> list[str]:
    if target_plugin_root.exists():
        shutil.rmtree(target_plugin_root)
    target_plugin_root.mkdir(parents=True)

    copied: list[str] = []
    for relative in SNAPSHOT_PATHS:
        source = source_root / relative
        if not source.exists():
            continue
        destination = target_plugin_root / relative
        if source.is_dir():
            shutil.copytree(
                source,
                destination,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"),
            )
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        copied.append(relative)

    manifest = target_plugin_root / ".codex-plugin" / "plugin.json"
    if not manifest.exists():
        raise SyncError("snapshot is missing .codex-plugin/plugin.json")
    return copied


def load_json(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise SyncError(f"missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SyncError(f"invalid JSON in {path}: {exc}") from exc


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def update_marketplace(mcskills_root: Path, plugin_manifest: dict) -> str:
    marketplace_path = mcskills_root / MARKETPLACE_PATH
    marketplace = load_json(marketplace_path)
    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list):
        raise SyncError("marketplace plugins must be a list")

    interface = plugin_manifest.get("interface")
    category = "Productivity"
    if isinstance(interface, dict) and interface.get("category"):
        category = str(interface["category"])

    entry = {
        "name": PLUGIN_NAME,
        "source": {
            "source": "local",
            "path": f"./plugins/{PLUGIN_NAME}",
        },
        "policy": {
            "installation": "AVAILABLE",
            "authentication": "ON_INSTALL",
        },
        "category": category,
    }

    for index, existing in enumerate(plugins):
        if isinstance(existing, dict) and existing.get("name") == PLUGIN_NAME:
            plugins[index] = entry
            write_json(marketplace_path, marketplace)
            return "updated"

    plugins.append(entry)
    write_json(marketplace_path, marketplace)
    return "added"


def sync(source_root: Path, mcskills_root: Path, release_tag: str | None) -> dict:
    source_root = source_root.resolve()
    mcskills_root = mcskills_root.resolve()
    manifest_path = source_root / ".codex-plugin" / "plugin.json"
    manifest = load_json(manifest_path)

    plugin_root = mcskills_root / "plugins" / PLUGIN_NAME
    copied = copy_snapshot(source_root, plugin_root)
    marketplace_action = update_marketplace(mcskills_root, manifest)

    return {
        "plugin": PLUGIN_NAME,
        "version": manifest.get("version"),
        "releaseTag": release_tag,
        "targetPath": str(plugin_root),
        "copied": copied,
        "marketplace": marketplace_action,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=".", help="LoopEngineer repository root")
    parser.add_argument("--target", required=True, help="MC-SKILLS repository root")
    parser.add_argument("--release-tag", help="GitHub Release tag that triggered the sync")
    args = parser.parse_args()

    try:
        result = sync(Path(args.source), Path(args.target), args.release_tag)
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
