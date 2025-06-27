"""
会话数据模型和存储接口
"""
from typing import Dict, List, Optional, Protocol
from pydantic import BaseModel
from datetime import datetime
import uuid
import json
import threading
import asyncio
import logging

logger = logging.getLogger(__name__)

class SessionState(BaseModel):
    """面试会话状态"""
    session_id: str
    job_description: str
    interview_type: str = "behavioral"  # behavioral/technical/situational
    history: List[Dict[str, str]] = []
    created_at: datetime = datetime.now()
    last_activity: datetime = datetime.now()
    is_completed: bool = False
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class SessionStorage(Protocol):
    """会话存储接口，支持内存和Redis实现"""
    
    async def create_session(
        self,
        job_description: str,
        interview_type: str = "behavioral",
        session_id: Optional[str] = None,
    ) -> SessionState:
        """创建新会话"""
        ...
    
    async def get_session(self, session_id: str) -> Optional[SessionState]:
        """获取会话"""
        ...
    
    async def update_session(self, session: SessionState) -> bool:
        """更新会话"""
        ...
    
    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        ...

class InMemorySessionStorage:
    """内存版会话存储 - 用于开发和演示，现在支持线程安全"""
    
    def __init__(self):
        self._sessions: Dict[str, SessionState] = {}
        self._lock = threading.RLock()  # 使用可重入锁，支持嵌套锁定
        self._stats = {
            "total_created": 0,
            "total_updated": 0,
            "total_deleted": 0,
            "access_errors": 0
        }
    
    async def create_session(
        self,
        job_description: str,
        interview_type: str = "behavioral",
        session_id: Optional[str] = None,
    ) -> SessionState:
        """创建新会话 - 线程安全版本"""
        try:
            session_id = session_id or str(uuid.uuid4())
            session = SessionState(
                session_id=session_id,
                job_description=job_description,
                interview_type=interview_type
            )
            
            with self._lock:
                # 检查会话ID是否已存在
                if session_id in self._sessions:
                    raise ValueError(f"会话ID {session_id} 已存在")
                
                self._sessions[session_id] = session
                self._stats["total_created"] += 1
                
            logger.debug(f"✅ 创建会话: {session_id}")
            return session
            
        except Exception as e:
            with self._lock:
                self._stats["access_errors"] += 1
            logger.error(f"❌ 创建会话失败: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[SessionState]:
        """获取会话 - 线程安全版本"""
        try:
            with self._lock:
                session = self._sessions.get(session_id)
                
                # 如果会话存在，更新最后访问时间
                if session:
                    session.last_activity = datetime.now()
                    
            return session
            
        except Exception as e:
            with self._lock:
                self._stats["access_errors"] += 1
            logger.error(f"❌ 获取会话失败 {session_id}: {e}")
            return None
    
    async def update_session(self, session: SessionState) -> bool:
        """更新会话 - 线程安全版本"""
        try:
            with self._lock:
                if session.session_id in self._sessions:
                    session.last_activity = datetime.now()
                    self._sessions[session.session_id] = session
                    self._stats["total_updated"] += 1
                    logger.debug(f"✅ 更新会话: {session.session_id}")
                    return True
                else:
                    logger.warning(f"⚠️ 尝试更新不存在的会话: {session.session_id}")
                    return False
                    
        except Exception as e:
            with self._lock:
                self._stats["access_errors"] += 1
            logger.error(f"❌ 更新会话失败 {session.session_id}: {e}")
            return False
    
    async def delete_session(self, session_id: str) -> bool:
        """删除会话 - 线程安全版本"""
        try:
            with self._lock:
                if session_id in self._sessions:
                    del self._sessions[session_id]
                    self._stats["total_deleted"] += 1
                    logger.debug(f"✅ 删除会话: {session_id}")
                    return True
                else:
                    logger.warning(f"⚠️ 尝试删除不存在的会话: {session_id}")
                    return False
                    
        except Exception as e:
            with self._lock:
                self._stats["access_errors"] += 1
            logger.error(f"❌ 删除会话失败 {session_id}: {e}")
            return False
    
    def get_stats(self) -> Dict[str, any]:
        """获取存储统计信息 - 线程安全"""
        try:
            with self._lock:
                return {
                    "session_count": len(self._sessions),
                    "total_created": self._stats["total_created"],
                    "total_updated": self._stats["total_updated"],
                    "total_deleted": self._stats["total_deleted"],
                    "access_errors": self._stats["access_errors"],
                    "storage_type": "memory"
                }
        except Exception as e:
            logger.error(f"❌ 获取统计信息失败: {e}")
            return {"error": str(e)}
    
    async def cleanup_expired_sessions(self, max_age_hours: int = 24) -> int:
        """清理过期会话"""
        try:
            cutoff_time = datetime.now() - datetime.timedelta(hours=max_age_hours)
            expired_sessions = []
            
            with self._lock:
                for session_id, session in list(self._sessions.items()):
                    if session.last_activity < cutoff_time:
                        expired_sessions.append(session_id)
                
                # 删除过期会话
                for session_id in expired_sessions:
                    del self._sessions[session_id]
                    self._stats["total_deleted"] += 1
            
            if expired_sessions:
                logger.info(f"🧹 清理了 {len(expired_sessions)} 个过期会话")
                
            return len(expired_sessions)
            
        except Exception as e:
            with self._lock:
                self._stats["access_errors"] += 1
            logger.error(f"❌ 清理过期会话失败: {e}")
            return 0
    
    async def list_sessions(self, limit: int = 100) -> List[Dict[str, any]]:
        """列出会话（用于调试）"""
        try:
            with self._lock:
                sessions = list(self._sessions.values())[:limit]
                return [
                    {
                        "session_id": session.session_id,
                        "interview_type": session.interview_type,
                        "created_at": session.created_at.isoformat(),
                        "last_activity": session.last_activity.isoformat(),
                        "is_completed": session.is_completed,
                        "history_length": len(session.history)
                    }
                    for session in sessions
                ]
        except Exception as e:
            logger.error(f"❌ 列出会话失败: {e}")
            return []

class RedisSessionStorage:
    """Redis版会话存储 - 用于生产环境，增强错误处理"""
    
    def __init__(self, redis_client, ttl: int = 3600):
        self.redis = redis_client
        self.ttl = ttl  # 会话过期时间(秒)
        self._lock = asyncio.Lock()  # 异步锁
        self._stats = {
            "total_created": 0,
            "total_updated": 0,
            "total_deleted": 0,
            "redis_errors": 0
        }
    
    async def create_session(
        self,
        job_description: str,
        interview_type: str = "behavioral",
        session_id: Optional[str] = None,
    ) -> SessionState:
        """创建新会话"""
        try:
            session_id = session_id or str(uuid.uuid4())
            session = SessionState(
                session_id=session_id,
                job_description=job_description,
                interview_type=interview_type
            )
            
            key = f"session:{session_id}"
            
            async with self._lock:
                # 检查会话是否已存在
                if await self.redis.exists(key):
                    raise ValueError(f"会话ID {session_id} 已存在")
                
                await self.redis.setex(key, self.ttl, session.json())
                self._stats["total_created"] += 1
                
            logger.debug(f"✅ Redis创建会话: {session_id}")
            return session
            
        except Exception as e:
            async with self._lock:
                self._stats["redis_errors"] += 1
            logger.error(f"❌ Redis创建会话失败: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[SessionState]:
        """获取会话"""
        try:
            key = f"session:{session_id}"
            data = await self.redis.get(key)
            
            if data:
                session = SessionState.parse_raw(data)
                
                # 更新最后活动时间并重新保存
                session.last_activity = datetime.now()
                await self.redis.setex(key, self.ttl, session.json())
                
                return session
            return None
            
        except Exception as e:
            async with self._lock:
                self._stats["redis_errors"] += 1
            logger.error(f"❌ Redis获取会话失败 {session_id}: {e}")
            return None
    
    async def update_session(self, session: SessionState) -> bool:
        """更新会话"""
        try:
            key = f"session:{session.session_id}"
            session.last_activity = datetime.now()
            
            # 检查key是否存在
            if await self.redis.exists(key):
                await self.redis.setex(key, self.ttl, session.json())
                async with self._lock:
                    self._stats["total_updated"] += 1
                logger.debug(f"✅ Redis更新会话: {session.session_id}")
                return True
            else:
                logger.warning(f"⚠️ 尝试更新不存在的Redis会话: {session.session_id}")
                return False
                
        except Exception as e:
            async with self._lock:
                self._stats["redis_errors"] += 1
            logger.error(f"❌ Redis更新会话失败 {session.session_id}: {e}")
            return False
    
    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        try:
            key = f"session:{session_id}"
            deleted = await self.redis.delete(key)
            
            if deleted > 0:
                async with self._lock:
                    self._stats["total_deleted"] += 1
                logger.debug(f"✅ Redis删除会话: {session_id}")
                return True
            else:
                logger.warning(f"⚠️ 尝试删除不存在的Redis会话: {session_id}")
                return False
                
        except Exception as e:
            async with self._lock:
                self._stats["redis_errors"] += 1
            logger.error(f"❌ Redis删除会话失败 {session_id}: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, any]:
        """获取Redis存储统计信息"""
        try:
            async with self._lock:
                stats = dict(self._stats)
                stats["storage_type"] = "redis"
                
                # 获取Redis信息
                try:
                    info = await self.redis.info()
                    stats["redis_memory_used"] = info.get("used_memory_human", "unknown")
                    stats["redis_connected_clients"] = info.get("connected_clients", 0)
                except:
                    stats["redis_info"] = "unavailable"
                
                return stats
                
        except Exception as e:
            logger.error(f"❌ Redis获取统计信息失败: {e}")
            return {"error": str(e), "storage_type": "redis"}

# 为了兼容性，创建InterviewSession别名
InterviewSession = SessionState

# 全局存储实例 - 可根据环境变量切换
# 生产环境中可以通过依赖注入配置
storage: SessionStorage = InMemorySessionStorage() 

# 添加存储健康检查
async def check_storage_health() -> Dict[str, any]:
    """检查存储健康状态"""
    try:
        # 创建测试会话
        test_session = await storage.create_session(
            job_description="健康检查测试",
            interview_type="technical",
            session_id="health_check_test"
        )
        
        # 获取会话
        retrieved_session = await storage.get_session("health_check_test")
        
        # 更新会话
        if retrieved_session:
            retrieved_session.history.append({"role": "system", "content": "健康检查"})
            await storage.update_session(retrieved_session)
        
        # 删除测试会话
        await storage.delete_session("health_check_test")
        
        # 获取统计信息
        if hasattr(storage, 'get_stats'):
            stats = storage.get_stats()
        else:
            stats = {"note": "统计信息不可用"}
        
        return {
            "status": "healthy",
            "test_result": "passed",
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"❌ 存储健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "test_result": "failed",
            "error": str(e)
        } 