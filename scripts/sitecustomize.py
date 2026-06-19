"""Runtime startup hooks for scripts executed from this directory."""
from __future__ import annotations

try:
    from console_compat import configure_console_output

    configure_console_output()
except Exception:
    # Startup hooks must never block the actual script.
    pass
