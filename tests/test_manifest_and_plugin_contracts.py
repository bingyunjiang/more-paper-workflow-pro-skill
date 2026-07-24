from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

import scripts.validate_skill_package as package_validator


class ManifestAndPluginContractsTest(unittest.TestCase):
    def test_top_level_manifest_routes_all_eight_steps(self):
        text = (ROOT / "manifest.yaml").read_text(encoding="utf-8")
        allowed = set(package_validator.yaml_axis_allowed(text, "step"))
        routes = package_validator.yaml_mapping(text, "step_routes")
        self.assertEqual(len(allowed), 8)
        self.assertEqual(allowed, set(routes))
        for target in routes.values():
            self.assertTrue((ROOT / target).is_file(), target)

    def test_step7_modes_and_operations_match_public_contract(self):
        manifest = (ROOT / "manifest.step7.yaml").read_text(encoding="utf-8")
        entry = (ROOT / "agents" / "step_7_entry.md").read_text(encoding="utf-8")
        writing_modes = (ROOT / "references" / "writing-modes.md").read_text(encoding="utf-8")
        modes = set(package_validator.yaml_axis_allowed(manifest, "mode"))
        operations = set(package_validator.yaml_axis_allowed(manifest, "operation"))
        self.assertEqual(modes, package_validator.PUBLIC_STEP7_MODES)
        self.assertEqual(operations, package_validator.STEP7_OPERATIONS)
        self.assertEqual(modes, set(package_validator.yaml_mapping(manifest, "mode_routes")))
        self.assertEqual(operations, set(package_validator.yaml_mapping(manifest, "operation_routes")))
        for mode in modes:
            self.assertIn(f"`{mode}`", entry)
            self.assertIn(f"`{mode}`", writing_modes)
        for operation in operations:
            self.assertIn(f"`{operation}`", writing_modes)

    def test_root_is_self_contained_codex_plugin(self):
        plugin = ROOT / ".codex-plugin" / "plugin.json"
        entry = ROOT / "skills" / "more-paper-workflow" / "SKILL.md"
        self.assertTrue(plugin.is_file())
        self.assertTrue(entry.is_file())
        self.assertIn("../../SKILL.md", entry.read_text(encoding="utf-8"))
        self.assertFalse(
            (ROOT / "plugins" / "more-paper-workflow" / ".codex-plugin" / "plugin.json").exists()
        )

    def test_full_package_structure_validation_passes(self):
        result = package_validator.scan_skill(ROOT)
        self.assertEqual(result["status"], "ok", result["failures"])


if __name__ == "__main__":
    unittest.main()
