#!/usr/bin/env python3
"""Compatibility entrypoint for the retired Pro client.

The project is now fully open-source and local. This wrapper forwards all
arguments to marksix_engine.py so old repository paths no longer contact a
private API or enforce trial/subscription limits.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "register":
        raise SystemExit("项目已改为免费开源本地版，不再需要注册、API Key 或会员。请直接运行 marksix_engine.py。")
    if len(sys.argv) > 1 and sys.argv[1] == "forecast":
        sys.argv[1] = "analyze"
        sys.argv = ["--csv" if arg == "--history" else arg for arg in sys.argv]
    runpy.run_path(str(Path(__file__).with_name("marksix_engine.py")), run_name="__main__")
