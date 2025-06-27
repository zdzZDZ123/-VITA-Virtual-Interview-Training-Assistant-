"""
Whisper模型管理器
负责自动检测、下载和管理Whisper模型
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import json
import shutil
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class WhisperModelManager:
    """Whisper模型管理器"""
    
    # 模型配置
    MODEL_SIZES = {
        "tiny": {"size_mb": 39, "repo": "Systran/faster-whisper-tiny"},
        "base": {"size_mb": 74, "repo": "Systran/faster-whisper-base"}, 
        "small": {"size_mb": 244, "repo": "Systran/faster-whisper-small"},
        "medium": {"size_mb": 769, "repo": "Systran/faster-whisper-medium"},
        "large": {"size_mb": 1550, "repo": "Systran/faster-whisper-large-v1"},
        "large-v2": {"size_mb": 1550, "repo": "Systran/faster-whisper-large-v2"},
        "large-v3": {"size_mb": 1550, "repo": "Systran/faster-whisper-large-v3"}
    }
    
    def __init__(self, model_dir: str = "whisper_download"):
        """初始化模型管理器"""
        self.project_root = Path(__file__).parent.parent.parent
        self.model_dir = self.project_root / model_dir
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # 下载状态
        self.download_in_progress = False
        self.download_progress = {}
        
        logger.info(f"📦 WhisperModelManager 初始化完成, 模型目录: {self.model_dir}")
    
    def find_local_model(self, model_size: str) -> Optional[Path]:
        """查找本地模型"""
        # 多个可能的位置
        potential_paths = [
            self.model_dir / model_size,
            Path.home() / ".cache" / "huggingface" / "hub" / f"__REMOVED_API_KEY__{model_size}",
            Path.cwd() / "whisper_download" / model_size,
        ]
        
        for path in potential_paths:
            if self._validate_model_path(path):
                logger.info(f"✅ 找到本地模型: {path}")
                return path
        
        logger.warning(f"❌ 未找到本地模型 {model_size}")
        logger.info(f"📍 搜索路径包括: {[str(p) for p in potential_paths]}")
        return None
    
    def _validate_model_path(self, path: Path) -> bool:
        """验证模型路径是否有效"""
        if not path.exists() or not path.is_dir():
            return False
        
        # 检查必要文件
        required_files = ["config.json"]
        optional_files = ["model.bin", "tokenizer.json", "vocabulary.txt"]
        
        # 必须有config.json
        if not all((path / f).exists() for f in required_files):
            return False
        
        # 至少有一个模型文件
        has_model = any((path / f).exists() for f in optional_files)
        return has_model
    
    async def ensure_model_available(self, model_size: str, auto_download: bool = True) -> Optional[Path]:
        """确保模型可用，必要时自动下载"""
        # 先检查本地
        local_path = self.find_local_model(model_size)
        if local_path:
            return local_path
        
        if not auto_download:
            logger.warning(f"⚠️ 模型 {model_size} 不存在，且自动下载已禁用")
            return None
        
        # 自动下载
        logger.info(f"📥 开始自动下载模型 {model_size}")
        success = await self.download_model_async(model_size)
        
        if success:
            return self.model_dir / model_size
        else:
            logger.error(f"❌ 模型下载失败")
            return None
    
    async def download_model_async(self, model_size: str) -> bool:
        """异步下载模型"""
        if self.download_in_progress:
            logger.warning("⏳ 已有下载任务进行中")
            return False
        
        if model_size not in self.MODEL_SIZES:
            logger.error(f"❌ 不支持的模型大小: {model_size}")
            return False
        
        self.download_in_progress = True
        self.download_progress[model_size] = 0
        
        try:
            # 运行下载脚本
            script_path = self.project_root / "scripts" / "download_faster_whisper.py"
            
            if not script_path.exists():
                logger.error(f"❌ 下载脚本不存在: {script_path}")
                return False
            
            # 使用线程池执行同步的下载操作
            loop = asyncio.get_running_loop()
            with ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(
                    executor,
                    self._run_download_script,
                    str(script_path),
                    model_size
                )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 下载模型时出错: {e}")
            return False
        finally:
            self.download_in_progress = False
    
    def _run_download_script(self, script_path: str, model_size: str) -> bool:
        """运行下载脚本（同步）"""
        import subprocess
        
        try:
            # 构建命令
            cmd = [sys.executable, script_path, model_size, "--verify"]
            
            logger.info(f"🚀 执行下载命令: {' '.join(cmd)}")
            
            # 执行下载
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root)
            )
            
            if result.returncode == 0:
                logger.info(f"✅ 模型 {model_size} 下载成功")
                return True
            else:
                logger.error(f"❌ 下载失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 执行下载脚本失败: {e}")
            return False
    
    def get_model_info(self, model_size: str) -> Dict[str, Any]:
        """获取模型信息"""
        if model_size not in self.MODEL_SIZES:
            return {}
        
        info = self.MODEL_SIZES[model_size].copy()
        info["installed"] = self.find_local_model(model_size) is not None
        info["path"] = str(self.find_local_model(model_size) or "")
        
        return info
    
    def list_available_models(self) -> Dict[str, Dict[str, Any]]:
        """列出所有可用模型"""
        models = {}
        for size in self.MODEL_SIZES:
            models[size] = self.get_model_info(size)
        return models
    
    def cleanup_cache(self) -> int:
        """清理缓存，返回释放的字节数"""
        freed_bytes = 0
        
        # 清理 huggingface 缓存
        hf_cache = Path.home() / ".cache" / "huggingface"
        if hf_cache.exists():
            for model_dir in hf_cache.glob("**/__REMOVED_API_KEY__*"):
                try:
                    size = sum(f.stat().st_size for f in model_dir.rglob("*") if f.is_file())
                    shutil.rmtree(model_dir)
                    freed_bytes += size
                    logger.info(f"🧹 清理缓存: {model_dir.name}")
                except Exception as e:
                    logger.error(f"清理失败: {e}")
        
        return freed_bytes


# 全局实例
_model_manager: Optional[WhisperModelManager] = None

def get_model_manager() -> WhisperModelManager:
    """获取全局模型管理器实例"""
    global _model_manager
    if _model_manager is None:
        _model_manager = WhisperModelManager()
    return _model_manager 