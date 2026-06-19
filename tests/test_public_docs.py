from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read_rel(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class PublicDocsTest(unittest.TestCase):
    def test_readme_has_three_public_entry_prompts(self):
        readme = read_rel("README.md")
        for token in [
            "定题入口",
            "直达下载入口",
            "写作入口",
            "examples/first-run/README.md",
            "examples/demo/step8-ai-trace-demo/",
            "python3 scripts/run_step8_ai_trace.py --project-root examples/demo/step8-ai-trace-demo",
        ]:
            self.assertIn(token, readme)

    def test_first_run_examples_exist(self):
        for rel in [
            "examples/first-run/README.md",
            "examples/first-run/step1-topic-sample.md",
            "examples/first-run/step5-download-summary.md",
            "examples/first-run/step7-writing-sample.md",
            "examples/demo/demo-script.md",
            "examples/demo/step8-ai-trace-demo/README.md",
            "examples/demo/step8-ai-trace-demo/论文初稿.md",
            "examples/showcase/diagnostic_summary_ai_trace_sample.md",
            "examples/showcase/revision_ledger_ai_trace_sample.json",
            "examples/showcase/step8_ai_trace_demo.md",
        ]:
            self.assertTrue((ROOT / rel).exists(), rel)

    def test_marketplace_manifest_exists(self):
        self.assertTrue((ROOT / ".claude-plugin/marketplace.json").exists())

    def test_skill_mentions_public_first_examples(self):
        skill = read_rel("SKILL.md")
        self.assertIn("Public-first entry examples", skill)
        self.assertIn("README 首屏", skill)

    def test_update_reminder_protocol_is_public_and_host_agnostic(self):
        protocol = read_rel("references/update-reminder-protocol.md")
        for token in [
            "更新提醒协议（宿主无关）",
            "显示文本 + 接收用户回复",
            "宿主若支持原生按钮/弹窗，优先使用原生选项交互",
            "若宿主不支持原生按钮/弹窗，则显示 `render_update_prompt.py` 生成的标准文本",
            "升级 / 本次跳过 / 今日不再提醒",
            "升级失败，但将继续使用当前本地版本",
            "python3 \"$SKILL_DIR/scripts/check_skill_update.py\" --json",
            "--record-choice snooze_today",
        ]:
            self.assertIn(token, protocol)

    def test_step8_ai_trace_runtime_state_source_is_publicly_documented(self):
        readme = read_rel("README.md")
        showcase = read_rel("examples/showcase/README.md")
        step8_entry = read_rel("agents/step_8_entry.md")

        for text in [readme, showcase, step8_entry]:
            self.assertIn(".skill-state/ai_trace_diagnostics.json", text)

        self.assertIn("runtime 状态源", readme)
        self.assertIn("artifact_passport.json", readme)
        self.assertIn("运行态状态源之一", showcase)
        self.assertIn("status_contract", step8_entry)

    def test_step8_ai_trace_demo_is_a_minimal_hands_on_recipe(self):
        demo = read_rel("examples/showcase/step8_ai_trace_demo.md")
        for token in [
            "## 最小目录结构",
            "demo-project/",
            "## 命令 1：进入项目目录",
            "## 命令 2：运行 Step 8 AI Trace 入口",
            "## 命令 3：检查产物",
            ".skill-state/ai_trace_diagnostics.json",
            "diagnostic_summary.md",
            "revision_ledger.json",
            "revision_ledger.md",
            "润色质量报告.md",
            "### Step 8 总判断",
            "### 统一状态契约",
        ]:
            self.assertIn(token, demo)

    def test_step8_ai_trace_demo_folder_is_copyable(self):
        demo = read_rel("examples/demo/step8-ai-trace-demo/README.md")
        draft = read_rel("examples/demo/step8-ai-trace-demo/论文初稿.md")
        self.assertIn("python3 scripts/run_step8_ai_trace.py --project-root examples/demo/step8-ai-trace-demo", demo)
        self.assertIn("论文初稿.md", demo)
        self.assertIn("值得注意的是", draft)
        self.assertIn("这里需要补文献", draft)


if __name__ == "__main__":
    unittest.main()
