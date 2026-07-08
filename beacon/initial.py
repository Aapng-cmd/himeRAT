#!/usr/bin/env python3
"""Legacy entrypoint — use stage1/run.py instead."""

import runpy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
runpy.run_path(str(Path(__file__).parent / "stage1" / "run.py"), run_name="__main__")
