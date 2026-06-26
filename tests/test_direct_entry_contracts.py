from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read_rel(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class DirectEntryContractsTest(unittest.TestCase):
    def test_entry_routing_keeps_single_public_entry_without_linear_lock(self):
        skill = read_rel("SKILL.md")
        readme = read_rel("README.md")

        self.assertIn("对外只保留一个主入口", skill)
        self.assertIn("任一 Step 仍可直接进入", skill)
        self.assertIn("入口收敛只影响对外发现层，不影响从任一 Step 直接进入", readme)

    def test_step_agents_define_direct_entry_contracts(self):
        for step in range(3, 9):
            matches = [
                p for p in (ROOT / "agents").glob(f"step_{step}_*.md")
                if not p.name.endswith("_entry.md")
            ]
            self.assertGreaterEqual(len(matches), 1, f"expected at least one main agent file for step {step}")
            text = matches[0].read_text(encoding="utf-8")
            self.assertIn("Direct-entry input contract", text, matches[0].name)
            self.assertRegex(text, r"不要求.*回跑|不要求.*补跑", matches[0].name)

    def test_checkpoint_protocol_is_not_linear_lock(self):
        skill = read_rel("SKILL.md")
        self.assertIn("Checkpoint 是“当前 Step 的输入与风险确认协议”，不是线性流程锁", skill)
        self.assertIn("不限制 Step 6/7 直接入口", skill)

        step6 = read_rel("agents/step_6_zotero.md")
        self.assertIn("CP-ZOTERO-WRITE` 不是 Step 6/7 的入口门", step6)
        self.assertIn("只读操作、计划生成、查重和 dry-run 不触发本 checkpoint", step6)

    def test_step5_defaults_to_serial_reliability(self):
        step5 = read_rel("agents/step_5_download.md")
        router = read_rel("scripts/unified_download_router.py")

        self.assertIn("默认串行可靠", step5)
        self.assertIn("--parallel-phase1", step5)
        self.assertIn("--parallel-phase1", router)
        self.assertIn("deprecated and ignored", router)
        self.assertIn("downloads are serialized to protect the CDP browser", router)
        self.assertIn("Phase 1: Sci-Hub", router)

    def test_step6_requires_mode_selection_before_write_planning(self):
        step6 = read_rel("agents/step_6_zotero.md")
        self.assertIn("进入 Step 6 后，必须先确认 Zotero 模式：`local` / `cloud` / `skip`", step6)
        self.assertIn("不得静默默认 cloud", step6)
        self.assertIn("plan-only", step6)


if __name__ == "__main__":
    unittest.main()
