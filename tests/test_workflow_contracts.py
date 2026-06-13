import json
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from workflow_contracts import (  # noqa: E402
    DownloadManifestItem,
    FigureEvidenceRecord,
    FigureIndexRecord,
    RetrievalCandidate,
    RetrievalIndexManifest,
    SearchResultRecord,
    as_chinese_papers,
    dois_from_download_items,
    figure_evidence_payload,
    figure_index_payload,
    load_search_records,
    normalize_doi,
    retrieval_candidates_payload,
    retrieval_manifest_payload,
    stable_source_id,
    write_workflow_json,
)


class WorkflowContractsTest(unittest.TestCase):
    def test_normalize_doi_variants(self):
        self.assertEqual(
            normalize_doi("https://doi.org/10.1016/j.test.2024.01.001."),
            "10.1016/j.test.2024.01.001",
        )
        self.assertEqual(normalize_doi("doi:10.1109/TEST.2024.123"), "10.1109/TEST.2024.123")

    def test_chinese_article_url_only_routes_to_manifest(self):
        record = SearchResultRecord.from_search_result({
            "title": "薄壁管弯曲回弹研究",
            "source": "wanfang",
            "article_url": "https://www.wanfangdata.com.cn/details/detail.do?_type=perio&id=test",
            "verification_status": "VERIFIED",
        })

        self.assertTrue(record.source_id.startswith("wanfang."))
        self.assertEqual(record.download_hint, "chinese_article_url")

        item = DownloadManifestItem.from_search_record(record)
        self.assertEqual(item.status, "ready")
        self.assertTrue(item.article_url.startswith("https://www.wanfangdata.com.cn/"))

    def test_warn_reject_fields_preserved(self):
        record = SearchResultRecord.from_search_result({
            "title": "Questionable paper",
            "source": "crossref",
            "doi": "10.1234/example",
            "verification_status": "WARN",
            "verification_confidence": "low",
            "warn_class": "metadata_mismatch",
        })

        self.assertEqual(record.verification_status, "WARN")
        self.assertEqual(record.verification_confidence, "low")
        self.assertEqual(record.warn_class, "metadata_mismatch")

    def test_workflow_json_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "workflow.json"
            records = [
                SearchResultRecord.from_search_result({
                    "title": "A DOI paper",
                    "source": "openalex",
                    "doi": "https://doi.org/10.5555/demo",
                    "year": "2024",
                }),
                SearchResultRecord.from_search_result({
                    "title": "A CNKI paper",
                    "source": "cnki",
                    "article_url": "https://kns.cnki.net/kcms/detail/detail.aspx?dbcode=CJFD&filename=demo",
                }),
            ]

            write_workflow_json(path, records, {"query": "demo"})
            data = json.loads(path.read_text(encoding="utf-8"))
            loaded = load_search_records(path)

        self.assertEqual(data["schema_version"], "workflow-contracts.v1")
        self.assertEqual(data["artifact_type"], "search_results")
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0].doi, "10.5555/demo")
        self.assertTrue(loaded[1].source_id.startswith("cnki."))

    def test_download_item_views(self):
        items = [
            DownloadManifestItem(title="English", doi="10.5555/demo", source="openalex"),
            DownloadManifestItem(
                title="中文",
                source="cnki",
                source_id=stable_source_id("cnki", "中文"),
                article_url="https://kns.cnki.net/kcms/detail/detail.aspx?filename=demo",
            ),
        ]

        self.assertEqual(dois_from_download_items(items), ["10.5555/demo"])
        chinese = as_chinese_papers(items)
        self.assertEqual(len(chinese), 1)
        self.assertEqual(chinese[0]["source"], "cnki")

    def test_retrieval_manifest_payload(self):
        manifest = RetrievalIndexManifest(
            generated_at="2026-06-14T10:00:00+08:00",
            index_levels=["lightweight", "pdf_chunk"],
            sources=["zotero_notes", "pdf_chunks"],
            item_count=12,
            chunk_count=34,
            notes="candidate retrieval only",
        )
        payload = retrieval_manifest_payload(manifest)
        self.assertEqual(payload["schema_version"], "retrieval-index.v1")
        self.assertEqual(payload["item_count"], 12)
        self.assertEqual(payload["index_levels"], ["lightweight", "pdf_chunk"])

    def test_retrieval_candidates_payload(self):
        candidates = [
            RetrievalCandidate(
                query_text="claim about heat transfer",
                step_context="7.7",
                candidate_item_key="ABC123",
                candidate_chunk_id="chunk-1",
                page="12",
                source_type="pdf_chunk",
                retrieval_score="0.92",
                match_reason="keyword overlap",
                requires_direct_verification=True,
                post_verify_status="",
            )
        ]
        payload = retrieval_candidates_payload(candidates, {"chapter": "ch3"})
        self.assertEqual(payload["schema_version"], "retrieval-candidates.v1")
        self.assertEqual(payload["metadata"]["chapter"], "ch3")
        self.assertEqual(payload["candidates"][0]["candidate_item_key"], "ABC123")
        self.assertTrue(payload["candidates"][0]["requires_direct_verification"])

    def test_figure_index_payload(self):
        records = [
            FigureIndexRecord(
                item_key="ABC123",
                figure_id="fig_3",
                figure_type="figure",
                page="12",
                caption="Temperature distribution under condition A",
                mentions_in_text=["As shown in Fig. 3"],
                source_type="caption_plus_text",
                collection_path=["ch3", "results"],
                paper_tier="T1",
            )
        ]
        payload = figure_index_payload(records, {"chapter": "ch3"})
        self.assertEqual(payload["schema_version"], "figure-index.v1")
        self.assertEqual(payload["records"][0]["figure_id"], "fig_3")
        self.assertEqual(payload["records"][0]["source_type"], "caption_plus_text")

    def test_figure_evidence_payload(self):
        records = [
            FigureEvidenceRecord(
                figure_id="fig_3",
                item_key="ABC123",
                claim_binding="claim-7",
                caption_support="partial",
                text_support="strong",
                visual_support="pending",
                evidence_status="text_caption_aligned",
                recommended_action="retain",
            )
        ]
        payload = figure_evidence_payload(records, {"step": "7.11"})
        self.assertEqual(payload["schema_version"], "figure-evidence.v1")
        self.assertEqual(payload["records"][0]["evidence_status"], "text_caption_aligned")
        self.assertEqual(payload["records"][0]["recommended_action"], "retain")


if __name__ == "__main__":
    unittest.main()
