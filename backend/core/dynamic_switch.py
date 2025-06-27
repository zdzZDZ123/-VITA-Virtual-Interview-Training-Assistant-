"""
动态切换模块
支持运行时动态切换主备角色
"""

import logging
from typing import Optional, Dict, Any
from core.config import config
from .qwen_llama_client import get_client_manager
from core.performance_monitor import get_performance_monitor

logger = logging.getLogger(__name__)

class DynamicSwitchManager:
    """动态切换管理器"""
    
    def __init__(self):
        self.client_manager = get_client_manager()
        self.performance_monitor = get_performance_monitor()
        self.current_primary = "qwen" if config.PREFER_QWEN else "llama"
        self.switch_history = []
    
    def get_current_primary(self) -> str:
        """获取当前主提供商"""
        return self.current_primary
    
    def switch_primary(self, new_primary: str, reason: str = "manual") -> bool:
        """
        切换主提供商
        
        Args:
            new_primary: 新的主提供商 ('llama' 或 'qwen')
            reason: 切换原因
            
        Returns:
            是否切换成功
        """
        if new_primary not in ['llama', 'qwen']:
            logger.error(f"无效的提供商: {new_primary}")
            return False
        
        if new_primary == self.current_primary:
            logger.info(f"已经是主提供商: {new_primary}")
            return True
        
        old_primary = self.current_primary
        
        # 更新配置
        config.PREFER_QWEN = (new_primary == 'qwen')
        
        # 更新客户端管理器偏好
        self.client_manager.set_preferences(
            prefer_qwen=config.PREFER_QWEN,
            fallback_enabled=config.USE_LLAMA_FALLBACK
        )
        
        # 记录切换
        self.current_primary = new_primary
        self.switch_history.append({
            "timestamp": logger.info(f"主提供商切换: {old_primary} -> {new_primary} (原因: {reason})"),
            "from": old_primary,
            "to": new_primary,
            "reason": reason
        })
        
        # 记录到性能监控
        self.performance_monitor.record_provider_switch(
            from_provider=old_primary,
            to_provider=new_primary,
            reason=reason,
            function_type="primary_switch"
        )
        
        logger.info(f"主提供商已切换到: {new_primary}")
        return True
    
    def __REMOVED_API_KEY__(self) -> Optional[str]:
        """
        基于性能自动切换主提供商
        
        Returns:
            如果发生切换，返回新的主提供商；否则返回None
        """
        # 获取性能统计
        summary = self.performance_monitor.get_performance_summary()
        providers = summary.get("providers", {})
        
        if not providers:
            return None
        
        # 计算每个提供商的综合得分
        scores = {}
        for provider, stats in providers.items():
            if provider not in ['llama', 'qwen']:
                continue
            
            total_score = 0
            total_weight = 0
            
            for func_type, func_stats in stats.get("functions", {}).items():
                # 成功率权重最高
                success_rate = func_stats.get("success_rate", 0)
                total_score += success_rate * 3
                total_weight += 3
                
                # 响应时间（越快越好）
                avg_duration = func_stats.get("recent_avg_duration", float('inf'))
                if avg_duration < float('inf'):
                    # 将响应时间转换为0-1的分数（假设3秒以上为0分）
                    time_score = max(0, 1 - avg_duration / 3)
                    total_score += time_score * 2
                    total_weight += 2
            
            if total_weight > 0:
                scores[provider] = total_score / total_weight
        
        if not scores:
            return None
        
        # 找出最佳提供商
        best_provider = max(scores, key=scores.get)
        best_score = scores[best_provider]
        
        # 当前主提供商的得分
        current_score = scores.get(self.current_primary, 0)
        
        # 如果最佳提供商不是当前主提供商，且得分差异超过阈值
        score_threshold = 0.2  # 20%的性能差异
        if best_provider != self.current_primary and best_score - current_score > score_threshold:
            logger.info(
                f"性能分析建议切换: {self.current_primary}(得分:{current_score:.2f}) -> "
                f"{best_provider}(得分:{best_score:.2f})"
            )
            
            if self.switch_primary(best_provider, f"__REMOVED_API_KEY__{best_score-current_score:.2f}"):
                return best_provider
        
        return None
    
    def get_switch_status(self) -> Dict[str, Any]:
        """获取切换状态"""
        return {
            "current_primary": self.current_primary,
            "prefer_qwen": config.PREFER_QWEN,
            "fallback_enabled": config.USE_LLAMA_FALLBACK,
            "auto_switch_enabled": config.ENABLE_AUTO_SWITCH,
            "switch_history": self.switch_history[-10:],  # 最近10次切换
            "performance_summary": self.performance_monitor.get_performance_summary()
        }
    
    def enable_auto_switch(self, enabled: bool = True):
        """启用/禁用自动切换"""
        config.ENABLE_AUTO_SWITCH = enabled
        logger.info(f"自动切换已{'启用' if enabled else '禁用'}")
    
    def enable_fallback(self, enabled: bool = True):
        """启用/禁用备份"""
        config.USE_LLAMA_FALLBACK = enabled
        self.client_manager.set_preferences(
            prefer_qwen=config.PREFER_QWEN,
            fallback_enabled=enabled
        )
        logger.info(f"备份方案已{'启用' if enabled else '禁用'}")


# 全局动态切换管理器
dynamic_switch_manager = DynamicSwitchManager()


def get_dynamic_switch_manager() -> DynamicSwitchManager:
    """获取全局动态切换管理器"""
    return dynamic_switch_manager