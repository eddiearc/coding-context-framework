from __future__ import annotations

import unittest

from tests.helpers import REPOSITORY


class CiContractTests(unittest.TestCase):
    def test_ci_runs_all_public_checks_and_pinned_scanner(self) -> None:
        workflow = (REPOSITORY / ".github/workflows/ci.yml").read_text()
        for command in (
            "scripts/check-context.sh",
            "scripts/check-publication.sh",
            "scripts/check-secrets.sh",
        ):
            self.assertIn(command, workflow)
        self.assertIn("v8.24.2", workflow)
        self.assertNotIn("gitleaks:latest", workflow)
        self.assertIn("actions/checkout@v7", workflow)
        self.assertIn("actions/setup-python@v6", workflow)
        self.assertIn("contents: read", workflow)

    def test_secret_check_requires_the_pinned_version(self) -> None:
        script = (REPOSITORY / "scripts/check-secrets.sh").read_text()
        self.assertIn("8.24.2", script)
        self.assertIn("--redact", script)


if __name__ == "__main__":
    unittest.main()
