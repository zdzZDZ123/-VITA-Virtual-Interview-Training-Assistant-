"""
Whisper模型诊断和修复工具
自动检测和修复Whisper模型问题
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any

# 添加backend目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from core.whisper_model_manager import WhisperModelManager
from core.config import config
from core.logger import logger

# 设置日志级别
logging.basicConfig(level=logging.INFO)

class WhisperModelFixer:
    """Whisper模型修复器"""
    
    def __init__(self):
        self.model_manager = WhisperModelManager()
        self.config = config.get_local_whisper_config()
        self.required_model = self.config.get("model_size", "medium")
        
    def diagnose(self) -> Dict[str, Any]:
        """诊断模型状态"""
        print("\n🔍 Whisper模型诊断工具")
        print("=" * 50)
        
        diagnosis = {
            "required_model": self.required_model,
            "issues": [],
            "recommendations": []
        }
        
        # 检查所有模型状态
        print("\n📊 模型状态:")
        all_models = self.model_manager.list_available_models()
        
        for model_size, info in all_models.items():
            status = "✅ 已安装" if info.get("installed") else "❌ 未安装"
            print(f"  - {model_size}: {status}")
            if info.get("installed"):
                print(f"    路径: {info.get('path')}")
            else:
                print(f"    大小: {info.get('size_mb')} MB")
        
        # 检查所需模型
        print(f"\n🎯 所需模型: {self.required_model}")
        
        model_info = self.model_manager.get_model_info(self.required_model)
        if not model_info.get("installed"):
            diagnosis["issues"].append(f"所需模型 {self.required_model} 未安装")
            diagnosis["recommendations"].append(f"下载 {self.required_model} 模型")
        
        # 检查faster-whisper和标准whisper
        try:
            import faster_whisper
            print("\n✅ faster-whisper 已安装")
        except ImportError:
            diagnosis["issues"].append("faster-whisper 未安装")
            diagnosis["recommendations"].append("安装 faster-whisper: pip install faster-whisper")
        
        try:
            import whisper
            print("✅ 标准 whisper 已安装")
        except ImportError:
            print("⚠️ 标准 whisper 未安装（可选）")
        
        # 检查模型目录
        model_dir = Path(self.model_manager.model_dir)
        print(f"\n📁 模型目录: {model_dir}")
        print(f"   存在: {'✅' if model_dir.exists() else '❌'}")
        
        if model_dir.exists():
            subdirs = list(model_dir.iterdir())
            print(f"   内容: {len(subdirs)} 个项目")
            for subdir in subdirs:
                if subdir.is_dir():
                    print(f"     - {subdir.name}")
        
        # 检查缓存目录
        cache_dir = Path.home() / ".cache" / "huggingface"
        if cache_dir.exists():
            print(f"\n💾 缓存目录: {cache_dir}")
            whisper_models = list(cache_dir.glob("**/__REMOVED_API_KEY__*"))
            if whisper_models:
                print(f"   找到 {len(whisper_models)} 个缓存模型")
        
        return diagnosis
    
    async def fix_async(self, auto_download: bool = True) -> bool:
        """异步修复问题"""
        diagnosis = self.diagnose()
        
        if not diagnosis["issues"]:
            print("\n✅ 未发现问题，模型状态良好！")
            return True
        
        print(f"\n🔧 发现 {len(diagnosis['issues'])} 个问题:")
        for issue in diagnosis["issues"]:
            print(f"  - {issue}")
        
        if not auto_download:
            print("\n⚠️ 自动下载已禁用，请手动解决上述问题")
            return False
        
        # 尝试自动修复
        print("\n🚀 开始自动修复...")
        
        # 下载所需模型
        model_info = self.model_manager.get_model_info(self.required_model)
        if not model_info.get("installed"):
            print(f"\n📥 下载模型 {self.required_model}...")
            model_path = await self.model_manager.ensure_model_available(
                self.required_model, 
                auto_download=True
            )
            
            if model_path:
                print(f"✅ 模型下载成功: {model_path}")
                return True
            else:
                print("❌ 模型下载失败")
                return False
        
        return True
    
    def fix(self, auto_download: bool = True) -> bool:
        """同步修复接口"""
        return asyncio.run(self.fix_async(auto_download))
    
    def verify(self) -> bool:
        """验证修复结果"""
        print("\n🔍 验证修复结果...")
        
        # 测试导入
        try:
            from core.speech import SpeechService
            service = SpeechService()
            print("✅ SpeechService 初始化成功")
            
            # 检查模型是否已加载
            if hasattr(service, 'local_whisper') and service.local_whisper:
                print("✅ Whisper模型加载成功")
                return True
            else:
                print("❌ Whisper模型未能成功加载")
                return False
                
        except Exception as e:
            print(f"❌ 验证失败: {e}")
            return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Whisper模型诊断和修复工具")
    parser.add_argument(
        "--no-download", 
        action="store_true", 
        help="禁用自动下载"
    )
    parser.add_argument(
        "--diagnose-only", 
        action="store_true", 
        help="仅诊断，不修复"
    )
    
    args = parser.parse_args()
    
    fixer = WhisperModelFixer()
    
    if args.diagnose_only:
        fixer.diagnose()
    else:
        success = fixer.fix(auto_download=not args.no_download)
        
        if success:
            # 验证修复结果
            if fixer.verify():
                print("\n🎉 修复成功，VITA实时语音面试已准备就绪！")
            else:
                print("\n⚠️ 修复可能未完全成功，请检查日志")
        else:
            print("\n❌ 修复失败，请手动解决问题")


if __name__ == "__main__":
    main() 