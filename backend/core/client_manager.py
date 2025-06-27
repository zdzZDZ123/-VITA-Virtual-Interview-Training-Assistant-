import asyncio
import logging
from typing import List, Optional
from core.qwen_llama_client import _client_registry

logger = logging.getLogger(__name__)

class ClientManager:
    """客户端管理器，负责统一管理和清理所有客户端"""
    
    def __init__(self):
        self._shutdown_event = asyncio.Event()
        self._is_shutting_down = False
    
    async def cleanup_all_clients(self) -> None:
        """清理所有注册的客户端"""
        if self._is_shutting_down:
            return
            
        self._is_shutting_down = True
        logger.info("🧹 开始清理所有客户端...")
        
        # 获取所有活跃的客户端
        clients = list(_client_registry)
        
        if not clients:
            logger.info("✅ 没有需要清理的客户端")
            return
        
        # 并发关闭所有客户端
        tasks = []
        for client in clients:
            try:
                if hasattr(client, 'aclose'):
                    tasks.append(asyncio.create_task(client.aclose()))
            except Exception as e:
                logger.warning(f"⚠️ 创建客户端关闭任务时出错: {e}")
        
        if tasks:
            try:
                # 等待所有客户端关闭，设置超时
                await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=30.0
                )
                logger.info(f"✅ 成功清理 {len(tasks)} 个客户端")
            except asyncio.TimeoutError:
                logger.warning("⚠️ 客户端清理超时，强制继续")
            except Exception as e:
                logger.error(f"❌ 清理客户端时出错: {e}")
        
        self._shutdown_event.set()
        logger.info("🏁 客户端清理完成")
    
    async def wait_for_shutdown(self) -> None:
        """等待清理完成"""
        await self._shutdown_event.wait()
    
    @property
    def is_shutting_down(self) -> bool:
        """检查是否正在关闭"""
        return self._is_shutting_down
    
    def get_active_clients_count(self) -> int:
        """获取活跃客户端数量"""
        return len(_client_registry)

# 全局客户端管理器实例
client_manager = ClientManager()

# 便捷函数
async def cleanup_all_clients():
    """清理所有客户端的便捷函数"""
    await client_manager.cleanup_all_clients()

def get_active_clients_count() -> int:
    """获取活跃客户端数量的便捷函数"""
    return client_manager.get_active_clients_count()