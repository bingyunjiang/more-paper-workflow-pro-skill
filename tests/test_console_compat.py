import io
import os
import sys
import unittest
from unittest.mock import patch


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT_DIR = os.path.join(ROOT, "scripts")
sys.path.insert(0, SCRIPT_DIR)

import console_compat  # noqa: E402


class EncodedStringIO(io.StringIO):
    def __init__(self, encoding: str):
        super().__init__()
        self._encoding = encoding

    @property
    def encoding(self):
        return self._encoding

    def reconfigure(self, **kwargs):
        self.reconfigure_kwargs = kwargs


class ConsoleCompatTest(unittest.TestCase):
    def test_auto_uses_unicode_for_utf8_stream(self):
        stream = EncodedStringIO("utf-8")
        with patch.dict(os.environ, {"MORE_PAPER_SYMBOLS": "auto"}, clear=False):
            self.assertTrue(console_compat.supports_unicode_symbols(stream))
            self.assertEqual(console_compat.symbol("ok"), "✅")

    def test_auto_uses_ascii_for_cp936_stream(self):
        stream = EncodedStringIO("cp936")
        with patch.dict(os.environ, {"MORE_PAPER_SYMBOLS": "auto"}, clear=False), \
             patch.object(console_compat.sys, "stdout", stream):
            self.assertFalse(console_compat.supports_unicode_symbols(stream))
            self.assertEqual(console_compat.symbol("ok"), "[OK]")

    def test_env_can_force_ascii_or_emoji(self):
        stream = EncodedStringIO("utf-8")
        with patch.object(console_compat.sys, "stdout", stream), \
             patch.dict(os.environ, {"MORE_PAPER_SYMBOLS": "ascii"}, clear=False):
            self.assertFalse(console_compat.supports_unicode_symbols())
            self.assertEqual(console_compat.symbol("fail"), "[FAIL]")

        with patch.object(console_compat.sys, "stdout", EncodedStringIO("cp936")), \
             patch.dict(os.environ, {"MORE_PAPER_SYMBOLS": "emoji"}, clear=False):
            self.assertTrue(console_compat.supports_unicode_symbols())
            self.assertEqual(console_compat.symbol("fail"), "❌")

    def test_fallback_stream_translates_status_symbols(self):
        stream = EncodedStringIO("cp936")
        with patch.object(console_compat.sys, "stdout", stream), \
             patch.dict(os.environ, {"MORE_PAPER_SYMBOLS": "auto"}, clear=False):
            console_compat.configure_console_output()
            print("✅ ok ❌ fail ⚠ warn 🎉 done → next")

        self.assertIn("[OK] ok [FAIL] fail [WARN] warn [DONE] done -> next", stream.getvalue())

    def test_ascii_mode_translates_even_on_utf8_stream(self):
        stream = EncodedStringIO("utf-8")
        with patch.object(console_compat.sys, "stdout", stream), \
             patch.dict(os.environ, {"MORE_PAPER_SYMBOLS": "ascii"}, clear=False):
            console_compat.configure_console_output()
            print("✅ ok → next")

        self.assertIn("[OK] ok -> next", stream.getvalue())

    def test_child_python_env_sets_utf8_backslashreplace(self):
        env = console_compat.configure_child_python_utf8_env({"EXISTING": "1"})

        self.assertEqual(env["EXISTING"], "1")
        self.assertEqual(env["PYTHONIOENCODING"], "utf-8:backslashreplace")


if __name__ == "__main__":
    unittest.main()
