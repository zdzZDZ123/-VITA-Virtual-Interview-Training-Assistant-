from typing import List, Type


def get_engines():
    """Return list of instantiated engine objects ordered by priority."""
    # 手动导入和注册引擎，避免循环导入
    engines = []
    
    # 尝试加载Edge-TTS引擎 (优先级1)
    try:
        from .edge_engine import EdgeTTSEngine
        engines.append(EdgeTTSEngine())
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"⚠️ EdgeTTSEngine加载失败: {e}")
    
    # 尝试加载Pyttsx3引擎 (优先级2，备用)
    try:
        from .pyttsx3_engine import Pyttsx3Engine
        engines.append(Pyttsx3Engine())
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"⚠️ Pyttsx3Engine加载失败: {e}")
    
    # 按优先级排序
    return sorted(engines, key=lambda e: e.priority) 