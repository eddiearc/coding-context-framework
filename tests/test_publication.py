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


if __name__ == "__main__":
    unittest.main()
