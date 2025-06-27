#!/usr/bin/env python
"""
Root-level entrypoint for the VITA backend.
This thin wrapper ensures that running `python main.py` from the project root
works out-of-the-box by forwarding execution to `backend/main.py` through
Uvicorn, after properly setting up the Python path.  

It allows newcomers to start the service using the familiar command:

    python main.py

Environment variables:
    PORT: Override the default listen port (default: 8000).
"""

import os
import sys
from pathlib import Path

# Resolve key paths
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"

# Prepend backend directory to PYTHONPATH so that `backend` becomes importable
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Optional: surface helpful message when backend folder is missing
if not BACKEND_DIR.exists():
    raise FileNotFoundError(
        "Backend directory not found at expected location: {}".format(BACKEND_DIR)
    )

# 暴露 FastAPI app 对象，便于 `uvicorn main:app` 直接查找
# 确保 backend 目录在 Python 路径中
sys.path.insert(0, str(BACKEND_DIR))

# 导入 backend.main 中的 app
try:
    from main import app
except ImportError:
    # 如果直接导入失败，尝试从 backend.main 导入
    import importlib.util
    spec = importlib.util.spec_from_file_location("backend_main", BACKEND_DIR / "main.py")
    backend_main = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(backend_main)
    app = backend_main.app

# Run the FastAPI application defined in backend.main using Uvicorn
if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info",
    ) 