from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from audit_doctoral_thesis_readiness import audit  # noqa: E402


def complete_map(draft: Path) -> dict:
    return {
        "schema_version": "doctoral-thesis-map.v1",
        "draft_sha256": hashlib.sha256(draft.read_bytes()).hexdigest(),
        "scope": "full_thesis",
        "central_research_problem": "在边界 B 下，方法 M 如何改善对象 O？",
        "research_questions": [{"id": "RQ1", "question": "M 是否有效？", "chapter_ids": ["C3"], "result_ids": ["R1"], "conclusion": "在 B 下有效", "status": "closed"}],
        "results": [{"id": "R1", "summary": "改善 10%", "evidence_anchors": ["T1"], "boundary": "B"}],
        "contributions": [{"id": "K1", "type": "method", "claim": "提出 M", "result_ids": ["R1"], "evidence_anchors": ["T1"], "chapter_ids": ["C3"], "nearest_work": "W", "novelty_boundary": "仅改进 X", "not_claimed": "不声称普适"}],
        "chapters": [{"id": "C3", "function": "检验 RQ1", "rq_ids": ["RQ1"], "claim_ids": ["CL1"], "evidence_anchors": ["T1"], "transition_from": "C2", "transition_to": "C4"}],
        "reproducibility": {"research_object": "O", "data_or_materials": "D", "variables_and_parameters": "P", "baselines": "W", "procedure": "S", "analysis_method": "A", "environment": "E", "na_reasons": []},
        "negative_and_conflicting_evidence": [{"item": "N", "treatment": "讨论"}],
        "cross_chapter_synthesis": [{"proposition": "P", "chapter_ids": ["C3"], "result_ids": ["R1"], "boundary": "B"}],
        "limitations_and_transfer_boundaries": ["B"],
        "authorial_decisions": [{"decision": "采用 M", "rationale": "R", "status": "author_confirmed"}],
        "unresolved_author_inputs": [],
    }


class DoctoralReadinessTest(unittest.TestCase):
    def test_complete_current_map_is_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            draft = Path(tmp) / "draft.md"
            draft.write_text("# 论文\n", encoding="utf-8")
            self.assertEqual(audit(draft, complete_map(draft), True)["status"], "doctoral_ready")

    def test_direct_entry_incomplete_map_is_provisional_not_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            draft = Path(tmp) / "draft.md"
            draft.write_text("# 局部章节\n", encoding="utf-8")
            payload = audit(draft, {"schema_version": "doctoral-thesis-map.v1"}, False)
            self.assertEqual(payload["status"], "provisional")

    def test_closed_mode_blocks_stale_map_and_author_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            draft = Path(tmp) / "draft.md"
            draft.write_text("# 论文\n", encoding="utf-8")
            mapping = complete_map(draft)
            mapping["draft_sha256"] = "stale"
            mapping["unresolved_author_inputs"] = ["确认贡献 K1"]
            payload = audit(draft, mapping, True)
            self.assertEqual(payload["status"], "blocked")
            self.assertIn("stale_map", {x["code"] for x in payload["findings"]})
            self.assertIn("unresolved_author_inputs", {x["code"] for x in payload["findings"]})

    def test_cli_blocked_returns_nonzero_and_writes_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            draft, mapping = root / "draft.md", root / "map.json"
            draft.write_text("# 论文\n", encoding="utf-8")
            mapping.write_text(json.dumps({"schema_version": "doctoral-thesis-map.v1"}), encoding="utf-8")
            out_json, out_md = root / "audit.json", root / "audit.md"
            result = subprocess.run([sys.executable, str(ROOT / "scripts/audit_doctoral_thesis_readiness.py"), str(draft), str(mapping), "--require-closed", "--output-json", str(out_json), "--output-md", str(out_md)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertTrue(out_json.exists())
            self.assertIn("blocked", out_md.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
