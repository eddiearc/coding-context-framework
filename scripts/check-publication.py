#!/usr/bin/env python3
"""Fail when a workspace contains material unsafe for a public template."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path


EXCLUDED_DIRECTORIES = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "venv",
    "node_modules",
}


def content_rules() -> tuple[tuple[str, re.Pattern[str]], ...]:
    slash = "/"
    private_home = slash + "Users" + slash
    unix_home = slash + "home" + slash
    windows_home = "C:" + "\\" + "Users" + "\\"
    private_path = re.compile(
        rf"(?:{re.escape(private_home)}|{re.escape(unix_home)})[^/\s]+/"
        rf"|{re.escape(windows_home)}[^\\\s]+\\",
        re.IGNORECASE,
    )

    private_suffixes = ("internal", "corp", "lan")
    suffix_pattern = "|".join(re.escape(item) for item in private_suffixes)
    internal_domain = re.compile(
        rf"\b(?:[a-z0-9-]+\.)+(?:{suffix_pattern})(?=\b|[:/])",
        re.IGNORECASE,
    )

    chat_key = "chat" + "_" + "id"
    chat_prefix = "oc" + "_"
    opaque_chat = re.compile(
        rf"\b{re.escape(chat_key)}\s*[:=]\s*{re.escape(chat_prefix)}"
        rf"[A-Za-z0-9]{{12,}}\b"
    )
    user_keys = ("open" + "_" + "id", "user" + "_" + "id")
    user_prefixes = ("ou" + "_", "on" + "_")
    opaque_user = re.compile(
        rf"\b(?:{'|'.join(map(re.escape, user_keys))})\s*[:=]\s*"
        rf"(?:{'|'.join(map(re.escape, user_prefixes))})[A-Za-z0-9]{{12,}}\b"
    )

    retired_key = "requirement" + "_" + "rows"
    retired_requirement_name = re.compile(rf"\b{re.escape(retired_key)}\b")

    return (
        ("private-path", private_path),
        ("internal-domain", internal_domain),
        ("opaque-chat-id", opaque_chat),
        ("opaque-user-id", opaque_user),
        ("legacy-requirement-key", retired_requirement_name),
    )


def sensitive_filename(path: Path) -> bool:
    name = path.name.lower()
    dot_env = "." + "env"
    exact = {
        dot_env,
        "credentials.json",
        "auth.json",
        "id_rsa",
        "id_ed25519",
        "cookies.txt",
    }
    if name in exact:
        return True
    if name.startswith(dot_env + ".") and name != dot_env + ".example":
        return True
    if name.startswith(("session", "memory")) and name.endswith(".json"):
        return True
    return path.suffix.lower() in {
        ".pem",
        ".key",
        ".p12",
        ".pfx",
        ".log",
        ".sqlite",
        ".db",
    }


def inside(root: Path, candidate: Path) -> bool:
    try:
        return os.path.commonpath((str(root), str(candidate))) == str(root)
    except ValueError:
        return False


def iter_workspace_paths(root: Path):
    for directory, directory_names, file_names in os.walk(root, followlinks=False):
        base = Path(directory)
        kept_directories: list[str] = []
        for name in directory_names:
            child = base / name
            if name in EXCLUDED_DIRECTORIES:
                continue
            yield child
            if not child.is_symlink():
                kept_directories.append(name)
        directory_names[:] = kept_directories
        for name in file_names:
            candidate = base / name
            if candidate.relative_to(root) == Path(".git"):
                continue
            yield candidate


def scan(root: Path) -> list[tuple[str, Path]]:
    violations: list[tuple[str, Path]] = []
    rules = content_rules()
    for path in iter_workspace_paths(root):
        relative = path.relative_to(root)
        if path.is_symlink():
            if not inside(root, path.resolve(strict=False)):
                violations.append(("escaping-symlink", relative))
            continue
        if not path.is_file():
            continue
        if sensitive_filename(path):
            violations.append(("sensitive-filename", relative))
            continue
        try:
            payload = path.read_bytes()
        except OSError:
            violations.append(("unreadable-file", relative))
            continue
        if b"\0" in payload:
            continue
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in rules:
            if pattern.search(text):
                violations.append((label, relative))
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="workspace to scan")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    if not root.is_dir():
        parser.error(f"not a directory: {args.root}")

    violations = scan(root)
    if violations:
        for label, path in sorted(set(violations)):
            print(f"publication violation [{label}]: {path}", file=sys.stderr)
        print(
            f"publication check failed: {len(set(violations))} violation(s)",
            file=sys.stderr,
        )
        return 1
    print("publication check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
