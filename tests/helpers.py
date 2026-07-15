from __future__ import annotations

import os
import subprocess
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]


def run(
    *args: os.PathLike[str] | str,
    cwd: Path | None = None,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [os.fspath(arg) for arg in args],
        cwd=cwd or REPOSITORY,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"command failed ({result.returncode}): {' '.join(map(os.fspath, args))}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def forbidden_samples() -> dict[str, tuple[str, str]]:
    """Build negative samples without publishing the forbidden values verbatim."""
    return {
        "private-path": ("notes.md", "/" + "Users" + "/sample-person/private/project\n"),
        "internal-domain": ("notes.md", "https://service" + "." + "internal/api\n"),
        "opaque-chat-id": ("notes.md", "chat" + "_id: " + "oc_" + "1234567890abcdef\n"),
        "opaque-user-id": ("notes.md", "open" + "_id: " + "ou_" + "1234567890abcdef\n"),
        "legacy-requirement-key": (
            "notes.md",
            "requirement" + "_" + "rows" + ": [synthetic]\n",
        ),
        "sensitive-filename": ("." + "env", "SAMPLE_VALUE=synthetic\n"),
    }
