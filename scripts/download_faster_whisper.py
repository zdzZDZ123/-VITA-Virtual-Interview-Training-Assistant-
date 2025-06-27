#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
离线Whisper模型下载脚本
自动下载faster-whisper模型到本地目录，支持离线部署
"""

import os
import sys
import argparse
import shutil
from pathlib import Path

def download_faster_whisper_model(model_size: str = "medium", force_download: bool = False):
    """下载faster-whisper模型到本地目录"""
    
    # 设置HuggingFace镜像源
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
    
    # 模型配置
    MODEL_MAPPING = {
        "tiny": "Systran/faster-whisper-tiny",
        "base": "Systran/faster-whisper-base", 
        "small": "Systran/faster-whisper-small",
        "medium": "Systran/faster-whisper-medium",
        "large": "Systran/faster-whisper-large-v1",
        "large-v2": "Systran/faster-whisper-large-v2",
        "large-v3": "Systran/faster-whisper-large-v3"
    }
    
    if model_size not in MODEL_MAPPING:
        print(f"❌ 不支持的模型大小: {model_size}")
        print(f"支持的模型: {list(MODEL_MAPPING.keys())}")
        return False
    
    # 设置路径
    project_root = Path(__file__).parent.parent
    whisper_download_dir = project_root / "whisper_download"
    model_dir = whisper_download_dir / model_size
    
    print(f"🚀 开始下载faster-whisper模型: {model_size}")
    print(f"📂 目标目录: {model_dir}")
    
    # 检查是否已存在
    if model_dir.exists() and not force_download:
        print(f"✅ 模型已存在: {model_dir}")
        print("使用 --force 参数强制重新下载")
        return True
    
    # 创建目录
    model_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # 尝试使用huggingface_hub下载
        try:
            from huggingface_hub import snapshot_download
            print("📦 使用 huggingface_hub 下载...")
            
            snapshot_download(
                repo_id=MODEL_MAPPING[model_size],
                local_dir=str(model_dir),
                local_dir_use_symlinks=False,
                resume_download=True
            )
            print(f"✅ 模型下载完成: {model_dir}")
            return True
            
        except ImportError:
            print("⚠️ huggingface_hub 未安装，尝试使用 git clone...")
            
        # 备用方案：使用git clone
        import subprocess
        repo_url = f"https://huggingface.co/{MODEL_MAPPING[model_size]}"
        
        result = subprocess.run([
            "git", "clone", repo_url, str(model_dir)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ 模型下载完成: {model_dir}")
            return True
        else:
            print(f"❌ git clone 失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        # 清理失败的下载
        if model_dir.exists():
            shutil.rmtree(model_dir)
        return False

def install_dependencies():
    """安装必要的依赖"""
    print("📦 检查并安装依赖...")
    
    try:
        import subprocess
        
        # 安装huggingface_hub
        try:
            import huggingface_hub
            print("✅ huggingface_hub 已安装")
        except ImportError:
            print("📥 安装 huggingface_hub...")
            subprocess.run([sys.executable, "-m", "pip", "install", "huggingface_hub"], check=True)
            print("✅ huggingface_hub 安装完成")
        
        # 安装faster-whisper
        try:
            import faster_whisper
            print("✅ faster-whisper 已安装")
        except ImportError:
            print("📥 安装 faster-whisper...")
            subprocess.run([sys.executable, "-m", "pip", "install", "faster-whisper"], check=True)
            print("✅ faster-whisper 安装完成")
            
        return True
        
    except Exception as e:
        print(f"❌ 依赖安装失败: {e}")
        return False

def verify_model(model_size: str):
    """验证下载的模型是否可用"""
    project_root = Path(__file__).parent.parent
    model_dir = project_root / "whisper_download" / model_size
    
    if not model_dir.exists():
        print(f"❌ 模型目录不存在: {model_dir}")
        return False
    
    try:
        print(f"🔍 验证模型: {model_size}")
        from faster_whisper import WhisperModel
        
        # 尝试加载模型
        model = WhisperModel(str(model_dir), device="cpu", compute_type="int8")
        print(f"✅ 模型验证成功: {model_size}")
        return True
        
    except Exception as e:
        print(f"❌ 模型验证失败: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="下载faster-whisper模型")
    parser.add_argument(
        "model_size", 
        nargs="?", 
        default="medium",
        choices=["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"],
        help="模型大小 (默认: medium)"
    )
    parser.add_argument("--force", action="store_true", help="强制重新下载")
    parser.add_argument("--verify", action="store_true", help="下载后验证模型")
    parser.add_argument("--install-deps", action="store_true", help="安装必要依赖")
    
    args = parser.parse_args()
    
    print("🚀 VITA faster-whisper 模型下载工具")
    print("=" * 50)
    
    # 安装依赖
    if args.install_deps:
        if not install_dependencies():
            sys.exit(1)
    
    # 下载模型
    success = download_faster_whisper_model(args.model_size, args.force)
    
    if not success:
        print("❌ 模型下载失败")
        sys.exit(1)
    
    # 验证模型
    if args.verify:
        if not verify_model(args.model_size):
            print("❌ 模型验证失败")
            sys.exit(1)
    
    print("\n🎉 模型准备完成！")
    print(f"📂 模型位置: whisper_download/{args.model_size}")
    print("现在可以启动VITA服务，将自动使用本地模型")

if __name__ == "__main__":
    main() 