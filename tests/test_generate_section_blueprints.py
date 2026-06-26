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
        self.assertIn("requires-mechanism-chain", mechanism_bp["risk_flags"])
        self.assertIn("变量传导", mechanism_bp["section_function"])


if __name__ == "__main__":
    unittest.main()
