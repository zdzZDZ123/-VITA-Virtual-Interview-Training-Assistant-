#!/usr/bin/env python
"""
VITA后端服务启动脚本
解决模块路径和环境变量问题
"""
import os
import sys
import uvicorn
from pathlib import Path

# 设置项目路径
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent

# 将backend目录添加到Python路径
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# 设置环境变量
os.environ["DISABLE_WHISPER_ONLINE"] = os.environ.get("DISABLE_WHISPER_ONLINE", "true")
os.environ["PYTHONPATH"] = str(BACKEND_DIR)

if __name__ == "__main__":
    print(f"🚀 启动VITA后端服务...")
    print(f"📁 Backend目录: {BACKEND_DIR}")
    print(f"📁 Python路径: {sys.path[:2]}")
    print(f"🌍 环境变量: DISABLE_WHISPER_ONLINE={os.environ.get('DISABLE_WHISPER_ONLINE')}")
    
    # 启动uvicorn服务
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )