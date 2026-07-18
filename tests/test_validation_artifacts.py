from __future__ import annotations

import unittest

from tests.helpers import REPOSITORY


class ValidationArtifactTests(unittest.TestCase):
    def test_document_defines_selectable_feedback_loops(self) -> None:
        document = (
            REPOSITORY / "docs/design-docs/layered-testing-practice.md"
        ).read_text()
        expected = (
            "Unit / Module tests",
            "evals",
            "structural checks",
            "Mock E2E",
            "Real CLI / Workflow",
            "Real API E2E",
            "Evidence / Demo",
        )
        for name in expected:
            with self.subTest(name=name):
                self.assertIn(name, document)
        self.assertIn("does not prove", document.lower())
        self.assertIn("synthetic", document.lower())
        self.assertIn("smallest effective feedback loop", document.lower())
        self.assertNotIn("report all seven layers", document.lower())

    def test_evidence_templates_exist_and_are_reproducible(self) -> None:
        template_dir = REPOSITORY / "docs/generated/evidence/templates"
        expected_columns = {
            "validation-report.md": ("Expected", "Actual", "Status", "Evidence"),
            "integration-cases.md": ("Case", "Environment", "Expected", "Actual"),
            "evidence-manifest.yaml": ("schema_version", "commands", "residual_risks"),
        }
        for filename, markers in expected_columns.items():
            path = template_dir / filename
            with self.subTest(filename=filename):
                self.assertTrue(path.is_file())
                content = path.read_text()
                for marker in markers:
                    self.assertIn(marker, content)


if __name__ == "__main__":
    unittest.main()
