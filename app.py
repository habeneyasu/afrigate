"""
Hugging Face Spaces entrypoint (Gradio).

Also runnable locally from the repo root::

    python app.py

Spaces set the ``PORT`` environment variable; we read it here. ``PYTHONPATH``
is not required when running from the repository root.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from ui.demo import CSS, demo


def main() -> None:
    port = int(os.environ.get("PORT", "7860"))
    demo.launch(
        server_name=os.environ.get("GRADIO_SERVER_NAME", "0.0.0.0"),
        server_port=port,
        share=False,
        css=CSS,
        show_error=True,
    )


if __name__ == "__main__":
    main()
