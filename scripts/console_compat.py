"""Console compatibility helpers for cross-platform CLI scripts."""
from __future__ import annotations

import os
import sys
from typing import TextIO


_EMOJI_SYMBOLS = {
    "ok": "✅",
    "fail": "❌",
    "warn": "⚠",
    "wait": "⏳",
    "skip": "⏭",
    "done": "🎉",
    "arrow": "→",
    "indent_arrow": "↳",
    "bullet": "•",
    "info": "ℹ",
}

_ASCII_SYMBOLS = {
    "ok": "[OK]",
    "fail": "[FAIL]",
    "warn": "[WARN]",
    "wait": "[WAIT]",
    "skip": "[SKIP]",
    "done": "[DONE]",
    "arrow": "->",
    "indent_arrow": "->",
    "bullet": "-",
    "info": "[INFO]",
}

_TEXT_REPLACEMENTS = {
    "✅": "[OK]",
    "❌": "[FAIL]",
    "⚠️": "[WARN]",
    "⚠": "[WARN]",
    "⏳": "[WAIT]",
    "⏭️": "[SKIP]",
    "⏭": "[SKIP]",
    "🎉": "[DONE]",
    "⛔": "[STOP]",
    "🚧": "[ACTION]",
    "🔐": "[LOGIN]",
    "📦": "[PKG]",
    "🔑": "[KEY]",
    "👤": "[USER]",
    "🚀": "[RUN]",
    "💻": "[DESKTOP]",
    "ℹ️": "[INFO]",
    "ℹ": "[INFO]",
    "⭐": "*",
    "📘": "*",
    "📄": "*",
    "⬜": "[ ]",
    "🎯": "[TARGET]",
    "📉": "[CHART]",
    "📊": "[CHART]",
    "📋": "[LIST]",
    "📚": "[DOCS]",
    "📁": "[DIR]",
    "📭": "[EMPTY]",
    "🔧": "[TOOL]",
    "🔍": "[SEARCH]",
    "🔎": "[SEARCH]",
    "🔴": "[RED]",
    "🟠": "[ORANGE]",
    "🟡": "[YELLOW]",
    "🟢": "[GREEN]",
    "🔵": "[BLUE]",
    "👆": "[CLICK]",
    "💡": "[TIP]",
    "🤖": "[BOT]",
    "🧩": "[PART]",
    "🌐": "[WEB]",
    "📝": "[NOTE]",
    "🎨": "[ART]",
    "🔌": "[PLUGIN]",
    "📌": "[PIN]",
    "→": "->",
    "↳": "->",
    "•": "-",
    "║": "|",
    "╔": "+",
    "╗": "+",
    "╚": "+",
    "╝": "+",
    "═": "=",
    "─": "-",
    "│": "|",
    "┌": "+",
    "┐": "+",
    "└": "+",
    "┘": "+",
    "–": "-",
    "—": "-",
}

_WRAPPED_ATTR = "_more_paper_console_wrapped"


def configure_console_output() -> None:
    """Prevent UnicodeEncodeError on legacy Windows consoles.

    The project uses Chinese progress text plus status symbols. On GBK/cp936
    consoles, emoji and some symbols cannot be encoded. Keep the active stream
    encoding, but make unencodable characters printable instead of fatal.
    """
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if getattr(stream, _WRAPPED_ATTR, False):
            continue
        reconfigure = getattr(stream, "reconfigure", None)
        if not callable(reconfigure):
            continue
        try:
            reconfigure(errors="backslashreplace")
        except Exception:
            try:
                reconfigure(errors="replace")
            except Exception:
                pass
        if should_translate_output(stream):
            setattr(sys, stream_name, _SymbolFallbackStream(stream))


def supports_unicode_symbols(stream: TextIO | None = None) -> bool:
    """Return whether status symbols should be emitted as Unicode."""
    mode = os.environ.get("MORE_PAPER_SYMBOLS", "auto").strip().lower()
    if mode in {"ascii", "plain", "text", "0", "false", "no"}:
        return False
    if mode in {"emoji", "unicode", "1", "true", "yes"}:
        return True

    stream = stream or sys.stdout
    encoding = (getattr(stream, "encoding", None) or "").lower()
    if not encoding:
        return False
    return "utf" in encoding


def should_translate_output(stream: TextIO | None = None) -> bool:
    """Return whether raw user-facing output should be translated to ASCII."""
    mode = os.environ.get("MORE_PAPER_SYMBOLS", "auto").strip().lower()
    if mode in {"ascii", "plain", "text", "0", "false", "no"}:
        return True
    if mode in {"emoji", "unicode", "1", "true", "yes"}:
        return False
    return not supports_unicode_symbols(stream)


def symbol(name: str) -> str:
    """Return a semantic status symbol suitable for the current console."""
    key = name.strip().lower().replace("-", "_")
    table = _EMOJI_SYMBOLS if supports_unicode_symbols() else _ASCII_SYMBOLS
    return table.get(key, _ASCII_SYMBOLS.get(key, name))


def replace_status_symbols(text: str) -> str:
    """Translate user-facing status glyphs to ASCII for legacy consoles."""
    for unicode_text, ascii_text in _TEXT_REPLACEMENTS.items():
        text = text.replace(unicode_text, ascii_text)
    return text


class _SymbolFallbackStream:
    """Text stream wrapper that translates status glyphs before writing."""

    def __init__(self, wrapped: TextIO):
        self._wrapped = wrapped
        setattr(self, _WRAPPED_ATTR, True)

    def write(self, text: str) -> int:
        translated = replace_status_symbols(text)
        return self._wrapped.write(translated)

    def writelines(self, lines) -> None:
        return self._wrapped.writelines(replace_status_symbols(line) for line in lines)

    def __getattr__(self, name: str):
        return getattr(self._wrapped, name)


def configure_child_python_utf8_env(env: dict[str, str] | None = None) -> dict[str, str]:
    """Return an environment that makes child Python text I/O UTF-8-safe."""
    child_env = dict(os.environ if env is None else env)
    child_env.setdefault("PYTHONIOENCODING", "utf-8:backslashreplace")
    return child_env


OK = symbol("ok")
FAIL = symbol("fail")
WARN = symbol("warn")
WAIT = symbol("wait")
SKIP = symbol("skip")
DONE = symbol("done")
ARROW = symbol("arrow")
BULLET = symbol("bullet")
INFO = symbol("info")
