"""Cloud entry point for Streamlit Community Cloud & Hugging Face Spaces.

Both platforms auto-detect a root-level `streamlit_app.py`. This shim puts the
project root on sys.path and launches the real dashboard under src/.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.dashboard.app import main  # noqa: E402  (must follow sys.path setup)

main()
