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
from doctoral_chapter_cycle import close, prepare  # noqa: E402


def mapping(draft: Path) -> dict:
    return {
        "schema_version": "doctoral-thesis-map.v1",
        "draft_sha256": hashlib.sha256(draft.read_bytes()).hexdigest(),
        "central_research_problem": "P",
        "chapters": [
            {"id": "C2", "claim_ids": ["CL0"], "result_ids": ["R0"], "writing_state": "closed", "actual_claim_ids": ["CL0"], "actual_result_ids": ["R0"]},
            {"id": "C3", "rq_ids": ["RQ1"], "claim_ids": ["CL1"], "result_ids": ["R1"], "contribution_ids": ["K1"], "evidence_anchors": ["T1"], "transition_from": "C2", "transition_to": "C4"},
            {"id": "C4", "claim_ids": ["CL2"], "result_ids": ["R2"]},
        ],
    }


def record(**changes) -> dict:
    value = {"actual_claim_ids": ["CL1"], "actual_result_ids": ["R1"], "actual_contribution_ids": ["K1"], "evidence_anchors": ["T1"], "boundary_updates": ["B"], "unresolved_questions": [], "next_chapter_obligations": ["承接 CL2"]}
    value.update(changes)
    return value


class DoctoralChapterCycleTest(unittest.TestCase):
    def test_prepare_freezes_global_and_later_chapter_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            draft = Path(tmp) / "draft.md"; draft.write_text("chapter", encoding="utf-8")
            snapshot = prepare(draft, mapping(draft), "C3")
            self.assertEqual(snapshot["status"], "prepared")
            self.assertEqual(snapshot["rq_ids"], ["RQ1"])
            self.assertEqual(snapshot["reserved_claim_owners"]["CL2"], "C4")
            self.assertEqual(snapshot["prior_chapter_closures"][0]["chapter_id"], "C2")

    def test_close_atomically_updates_only_current_chapter_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            draft = Path(tmp) / "draft.md"; draft.write_text("chapter", encoding="utf-8")
            original = mapping(draft); updated, report = close(draft, original, prepare(draft, original, "C3"), record())
            self.assertEqual(report["status"], "closed")
            c3 = next(x for x in updated["chapters"] if x["id"] == "C3")
            self.assertEqual(c3["actual_claim_ids"], ["CL1"])
            self.assertEqual(original["chapters"][1].get("writing_state"), None)
            self.assertEqual(updated["chapters"][2], original["chapters"][2])

    def test_close_rejects_later_claim_unregistered_result_and_contribution_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            draft = Path(tmp) / "draft.md"; draft.write_text("chapter", encoding="utf-8")
            original = mapping(draft)
            updated, report = close(draft, original, prepare(draft, original, "C3"), record(actual_claim_ids=["CL2"], actual_result_ids=["RX"], actual_contribution_ids=["KX"]))
            self.assertEqual(report["status"], "conflict")
            self.assertIs(updated, original)
            codes = {x["code"] for x in report["findings"]}
            self.assertTrue({"later_chapter_claim_taken", "unregistered_result", "contribution_boundary_drift"} <= codes)

    def test_close_rejects_stale_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            draft = Path(tmp) / "draft.md"; draft.write_text("chapter", encoding="utf-8")
            original = mapping(draft); snapshot = prepare(draft, original, "C3")
            original["central_research_problem"] = "changed"
            _, report = close(draft, original, snapshot, record())
            self.assertIn("stale_snapshot", {x["code"] for x in report["findings"]})

    def test_cli_conflict_does_not_rewrite_map(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); draft = root / "draft.md"; draft.write_text("chapter", encoding="utf-8")
            map_path, snapshot_path, record_path = root / "map.json", root / "snapshot.json", root / "record.json"
            map_path.write_text(json.dumps(mapping(draft), ensure_ascii=False), encoding="utf-8")
            subprocess.run([sys.executable, str(ROOT / "scripts/doctoral_chapter_cycle.py"), "prepare", str(draft), str(map_path), "C3", str(snapshot_path)], check=True, capture_output=True, text=True)
            before = map_path.read_bytes(); record_path.write_text(json.dumps(record(actual_claim_ids=["CL2"]), ensure_ascii=False), encoding="utf-8")
            result = subprocess.run([sys.executable, str(ROOT / "scripts/doctoral_chapter_cycle.py"), "close", str(draft), str(map_path), str(snapshot_path), str(record_path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(map_path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
