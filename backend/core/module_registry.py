"""
VITA 核心模块注册表
统一管理语音相关模块的导入、初始化和状态检查
"""

import logging
import sys
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ModuleStatus(Enum):
    """模块状态枚举"""
    NOT_INSTALLED = "not_installed"
    INSTALLED = "installed" 
    AVAILABLE = "available"
    ERROR = "error"
    READY = "ready"

@dataclass
class ModuleInfo:
    """模块信息数据类"""
    name: str
    status: ModuleStatus
    version: Optional[str] = None
    path: Optional[str] = None
    error_message: Optional[str] = None
    dependencies: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "version": self.version,
            "path": self.path,
            "error_message": self.error_message,
            "dependencies": self.dependencies or []
        }

class ModuleRegistry:
    """模块注册表 - 管理所有语音相关模块"""
    
    def __init__(self):
        self._modules: Dict[str, ModuleInfo] = {}
        self._module_instances: Dict[str, Any] = {}
        self._initialized = False
        
    def register_module(self, name: str, import_path: str, dependencies: List[str] = None) -> ModuleInfo:
        """注册模块"""
        logger.info(f"📦 注册模块: {name}")
        
        info = ModuleInfo(
            name=name,
            status=ModuleStatus.NOT_INSTALLED,
            dependencies=dependencies or []
        )
        
        try:
            # 尝试导入模块
            if name == "faster-whisper":
                import faster_whisper
                info.version = getattr(faster_whisper, '__version__', 'unknown')
                info.status = ModuleStatus.INSTALLED
                logger.info(f"✅ {name} 导入成功, 版本: {info.version}")
                
            elif name == "whisper":
                import whisper
                info.version = getattr(whisper, '__version__', 'unknown') 
                info.status = ModuleStatus.INSTALLED
                logger.info(f"✅ {name} 导入成功, 版本: {info.version}")
                
            elif name == "edge-tts":
                import edge_tts
                info.version = getattr(edge_tts, '__version__', 'unknown')
                info.status = ModuleStatus.INSTALLED
                logger.info(f"✅ {name} 导入成功, 版本: {info.version}")
                
            elif name == "pyttsx3":
                import pyttsx3
                info.version = getattr(pyttsx3, '__version__', 'unknown')
                info.status = ModuleStatus.INSTALLED
                logger.info(f"✅ {name} 导入成功, 版本: {info.version}")
                
        except ImportError as e:
            info.status = ModuleStatus.NOT_INSTALLED
            info.error_message = str(e)
            logger.warning(f"⚠️ {name} 未安装: {e}")
            
        except Exception as e:
            info.status = ModuleStatus.ERROR
            info.error_message = str(e)
            logger.error(f"❌ {name} 导入错误: {e}")
        
        self._modules[name] = info
        return info
    
    def get_module_status(self, name: str) -> Optional[ModuleInfo]:
        """获取模块状态"""
        return self._modules.get(name)
    
    def get_all_modules(self) -> Dict[str, ModuleInfo]:
        """获取所有模块状态"""
        return self._modules.copy()
    
    def is_module_available(self, name: str) -> bool:
        """检查模块是否可用"""
        info = self._modules.get(name)
        return info and info.status in [ModuleStatus.INSTALLED, ModuleStatus.AVAILABLE, ModuleStatus.READY]
    
    def check_dependencies(self) -> Dict[str, bool]:
        """检查所有依赖是否满足"""
        results = {}
        
        for name, info in self._modules.items():
            if info.dependencies:
                all_deps_met = all(
                    self.is_module_available(dep) for dep in info.dependencies
                )
                results[name] = all_deps_met
            else:
                results[name] = self.is_module_available(name)
                
        return results
    
    def initialize_all(self) -> bool:
        """初始化所有模块"""
        if self._initialized:
            return True
            
        logger.info("🚀 开始初始化所有语音模块...")
        
        # 按依赖顺序初始化
        success_count = 0
        total_count = len(self._modules)
        
        for name, info in self._modules.items():
            try:
                if info.status == ModuleStatus.INSTALLED:
                    # 这里可以添加模块特定的初始化逻辑
                    self._initialize_module(name)
                    info.status = ModuleStatus.READY
                    success_count += 1
                    logger.info(f"✅ {name} 初始化成功")
                    
            except Exception as e:
                info.status = ModuleStatus.ERROR
                info.error_message = f"初始化失败: {e}"
                logger.error(f"❌ {name} 初始化失败: {e}")
        
        self._initialized = success_count > 0
        logger.info(f"📊 模块初始化完成: {success_count}/{total_count} 成功")
        return self._initialized
    
    def _initialize_module(self, name: str):
        """初始化特定模块"""
        # 这里可以添加模块特定的初始化代码
        pass
    
    def get_health_report(self) -> Dict[str, Any]:
        """获取健康报告"""
        ready_modules = [name for name, info in self._modules.items() 
                        if info.status == ModuleStatus.READY]
        error_modules = [name for name, info in self._modules.items() 
                        if info.status == ModuleStatus.ERROR]
        
        return {
            "total_modules": len(self._modules),
            "ready_modules": len(ready_modules),
            "error_modules": len(error_modules),
            "ready_list": ready_modules,
            "error_list": error_modules,
            "initialized": self._initialized,
            "modules": {name: info.to_dict() for name, info in self._modules.items()}
        }
    
    def reload_module(self, name: str) -> bool:
        """重新加载模块"""
        logger.info(f"🔄 重新加载模块: {name}")
        
        if name in self._modules:
            # 移除旧的模块信息
            del self._modules[name]
            if name in self._module_instances:
                del self._module_instances[name]
        
        # 重新注册
        # 这里需要根据实际模块调整import_path
        return self.register_module(name, f"import {name}").status != ModuleStatus.ERROR

# 全局模块注册表实例
_registry: Optional[ModuleRegistry] = None

def get_module_registry() -> ModuleRegistry:
    """获取全局模块注册表"""
    global _registry
    if _registry is None:
        _registry = ModuleRegistry()
        # 注册核心模块
        _registry.register_module("faster-whisper", "faster_whisper")
        _registry.register_module("whisper", "whisper")
        _registry.register_module("edge-tts", "edge_tts") 
        _registry.register_module("pyttsx3", "pyttsx3")
        
        # 初始化所有模块
        _registry.initialize_all()
        
    return _registry

def check_voice_modules_health() -> Dict[str, Any]:
    """检查语音模块健康状态"""
    registry = get_module_registry()
    return registry.get_health_report()

def is_voice_module_available(module_name: str) -> bool:
    """检查指定语音模块是否可用"""
    registry = get_module_registry()
    return registry.is_module_available(module_name) 