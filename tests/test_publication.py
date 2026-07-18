from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from tests.helpers import REPOSITORY, forbidden_samples, run


class PublicationTests(unittest.TestCase):
    def test_repository_passes_publication_gate(self) -> None:
        result = run(REPOSITORY / "scripts/check-publication.sh", "--root", REPOSITORY)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_each_generated_negative_is_rejected(self) -> None:
        for case, (filename, content) in forbidden_samples().items():
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / filename).write_text(content)
                result = run(REPOSITORY / "scripts/check-publication.sh", "--root", root)
                self.assertNotEqual(0, result.returncode)
                self.assertIn(case, result.stdout + result.stderr)

    def test_escaping_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "workspace"
            outside = Path(directory) / "outside.txt"
            root.mkdir()
            outside.write_text("synthetic\n")
            os.symlink(outside, root / "external-link")
            result = run(REPOSITORY / "scripts/check-publication.sh", "--root", root)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("escaping-symlink", result.stdout + result.stderr)

    def test_worktree_git_metadata_file_is_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            slash = "/"
            (root / ".git").write_text(
                "gitdir: "
                + slash
                + "Users"
                + slash
                + "example/repository/.git/worktrees/example\n"
            )
            result = run(REPOSITORY / "scripts/check-publication.sh", "--root", root)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_excluded_directory_names_as_regular_files_are_scanned(self) -> None:
        slash = "/"
        private_path = slash + "Users" + slash + "example/private.txt\n"
        cases = (
            "nested/.git",
            "venv",
            "nested/venv",
            ".venv",
            "nested/.venv",
            "node_modules",
            "nested/node_modules",
        )
        for relative in cases:
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                forged = root / relative
                forged.parent.mkdir(parents=True, exist_ok=True)
                forged.write_text(private_path)
                result = run(
                    REPOSITORY / "scripts/check-publication.sh", "--root", root
                )
                self.assertNotEqual(0, result.returncode)
                self.assertIn("private-path", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
