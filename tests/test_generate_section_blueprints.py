from pathlib import Path
import sys
import tempfile
import unittest


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from generate_section_blueprints import generate_blueprints  # noqa: E402


class GenerateSectionBlueprintsTest(unittest.TestCase):
    def test_mechanism_section_gets_mechanism_evidence_requirements(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outline = root / "大纲关键词.md"
            style = root / "style_profile.md"
            evidence = root / "综述矩阵.csv"

            outline.write_text(
                "# 论文大纲\n\n## 1. 绪论\n\n## 2. 快充热失控机理分析\n",
                encoding="utf-8",
            )
            style.write_text("平均句长 20 words\n", encoding="utf-8")
            evidence.write_text(
                "作者年份,核心发现,方法,贡献,可引用摘录,与我的主题关系\n"
                "Wang2024,fast charging heat transfer,experiment,mechanism,quote,direct\n",
                encoding="utf-8",
            )

            blueprints = generate_blueprints(str(outline), str(style), str(evidence))

        mechanism_bp = blueprints[1].to_schema_dict()
        self.assertIn("mechanism_chain", mechanism_bp["evidence_needed"])
        self.assertIn("model_or_equation", mechanism_bp["evidence_needed"])
        self.assertIn("boundary_condition", mechanism_bp["evidence_needed"])
        self.assertIn("变量-作用路径证据", mechanism_bp["evidence_needed"])
        self.assertIn("机制判别图/表", mechanism_bp["evidence_needed"])
        self.assertIn("requires-mechanism-chain", mechanism_bp["risk_flags"])
        self.assertIn("变量传导", mechanism_bp["section_function"])

    def test_mechanism_judgement_and_path_terms_trigger_mechanism_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outline = root / "大纲关键词.md"
            style = root / "style_profile.md"
            evidence = root / "综述矩阵.csv"

            outline.write_text(
                "# 论文大纲\n\n## 1. 温度与应变速率的主导因素及演化路径\n",
                encoding="utf-8",
            )
            style.write_text("平均句长 20 words\n", encoding="utf-8")
            evidence.write_text("作者年份,核心发现,方法,贡献,可引用摘录,与我的主题关系\n", encoding="utf-8")

            blueprints = generate_blueprints(str(outline), str(style), str(evidence))

        mechanism_bp = blueprints[0].to_schema_dict()
        self.assertIn("mechanism_discrimination", mechanism_bp["section_function"])
        self.assertIn("主导机制", " ".join(mechanism_bp["key_claims"]))

    def test_non_mechanism_analysis_title_does_not_trigger(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outline = root / "大纲关键词.md"
            style = root / "style_profile.md"
            evidence = root / "综述矩阵.csv"

            outline.write_text(
                "# 论文大纲\n\n## 1. 参数优化结果分析\n",
                encoding="utf-8",
            )
            style.write_text("平均句长 20 words\n", encoding="utf-8")
            evidence.write_text("作者年份,核心发现,方法,贡献,可引用摘录,与我的主题关系\n", encoding="utf-8")

            blueprints = generate_blueprints(str(outline), str(style), str(evidence))

        bp = blueprints[0].to_schema_dict()
        self.assertNotIn("mechanism_chain", bp["evidence_needed"])
        self.assertNotIn("requires-mechanism-chain", bp["risk_flags"])

    def test_weak_influence_phrase_without_path_or_reason_does_not_trigger(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outline = root / "大纲关键词.md"
            style = root / "style_profile.md"
            evidence = root / "综述矩阵.csv"

            outline.write_text(
                "# 论文大纲\n\n## 1. 影响因素分析\n",
                encoding="utf-8",
            )
            style.write_text("平均句长 20 words\n", encoding="utf-8")
            evidence.write_text("作者年份,核心发现,方法,贡献,可引用摘录,与我的主题关系\n", encoding="utf-8")

            blueprints = generate_blueprints(str(outline), str(style), str(evidence))

        bp = blueprints[0].to_schema_dict()
        self.assertNotIn("mechanism_chain", bp["evidence_needed"])


if __name__ == "__main__":
    unittest.main()
