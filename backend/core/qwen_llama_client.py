"""豆包、Qwen & Llama API客户端模块
提供统一的豆包、Qwen和Llama API调用接口
使用httpx作为HTTP客户端，完全去除OpenAI依赖
支持豆包优先+Qwen+Llama的三模型架构
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
import urllib.request
import json
import time
from datetime import datetime
from contextlib import asynccontextmanager
import weakref
import httpx
from core.error_handler import with_retry, RetryConfig, ErrorCategory, log_error

# 导入OpenAI客户端用于兼容性
try:
    from openai import AsyncOpenAI
except ImportError:
    logger.warning("OpenAI库未安装，将使用Mock客户端")
    AsyncOpenAI = None

logger = logging.getLogger(__name__)

# 全局客户端注册表，用于清理
_client_registry = weakref.WeakSet()

def create_http_client(api_key: str, base_url: Optional[str] = None):
    """Create a client that supports Llama and Qwen APIs using httpx.

    Args:
        api_key: Llama or Qwen API key.
        base_url: Optional base URL for the API (used for Llama).

    Returns:
        An object exposing ``chat.completions.create`` and ``audio.*`` compatible interface.
    """
    return LazyHTTPClient(api_key, base_url)


class LazyHTTPClient:
    """延迟初始化的HTTP客户端包装器
    支持Llama、Qwen双模型架构和健康检查
    """
    
    def __init__(self, api_key: str, base_url: Optional[str] = None, **kwargs):
        self.api_key = api_key
        self.base_url = base_url
        self._client = None
        self._client_type = None  # 记录客户端类型
        self._last_health_check = 0
        self._health_check_interval = 300  # 5分钟检查一次
        self._is_healthy = True
        self._retry_count = 0
        self._max_retries = 3
        self._connection_timeout = kwargs.get('timeout', 30.0)
        self._max_retries_per_request = kwargs.get('max_retries', 3)
        self._is_closing = False
        
        # 警告：过滤掉可能导致问题的参数
        if kwargs:
            logger.debug(f"🔧 过滤掉可能不兼容的参数: {list(kwargs.keys())}")
        
        # 注册到全局清理列表
        _client_registry.add(self)
        
        logger.debug(f"🔧 初始化LazyOpenAIClient: timeout={self._connection_timeout}s")
        
    async def get_healthy_client(self):
        """获取健康的客户端，如果当前客户端不健康则尝试重新初始化"""
        # 如果正在关闭，直接返回错误
        if self._is_closing:
            raise Exception("客户端正在关闭中，无法使用")
            
        # 先初始化客户端
        client = self._get_client()
        
        # 检查健康状态
        if not await self._health_check():
            # 如果不健康且重试次数未超过最大值，尝试重新初始化
            if self._retry_count <= self._max_retries:
                logger.warning(f"⚠️ {self._client_type}客户端不健康，尝试重新初始化 (重试次数: {self._retry_count})")
                
                # 清理旧客户端
                await self.aclose()
                
                # 重置关闭状态，允许重新初始化
                self._is_closing = False
                
                # 重新初始化
                self._client = None
                client = self._get_client()
                
                # 再次检查健康状态
                if await self._health_check():
                    logger.info(f"✅ {self._client_type}客户端重新初始化成功")
                    return client
                else:
                    # 增加指数退避重试延迟
                    retry_delay = min(2 ** self._retry_count, 60)
                    logger.warning(f"⏱️ {self._client_type}客户端重新初始化失败，等待 {retry_delay} 秒后重试")
                    await asyncio.sleep(retry_delay)
                    
                    # 最后一次尝试
                    if self._retry_count >= self._max_retries:
                        logger.error(f"❌ {self._client_type}客户端重试次数已达上限 ({self._max_retries})")
                        raise Exception(f"{self._client_type}客户端不健康，重试次数已达上限")
                    
                    # 递归调用自身再次尝试
                    return await self.get_healthy_client()
            else:
                logger.error(f"❌ {self._client_type}客户端重试次数已达上限 ({self._max_retries})")
                raise Exception(f"{self._client_type}客户端不健康，重试次数已达上限")
        
        return client
        
    def _validate_api_key(self, api_key: str) -> str:
        """验证API密钥并返回客户端类型，失败时返回mock而不抛出异常"""
        if not api_key or not api_key.strip():
            logger.warning("API密钥为空，将使用Mock客户端")
            return 'mock'
        
        key = api_key.strip()
        
        # 豆包API密钥格式：UUID格式的字符串（8-4-4-4-12格式）
        if len(key) == 36 and key.count('-') == 4:
            # 验证UUID格式：__REMOVED_API_KEY__
            import re
            uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
            if uuid_pattern.match(key):
                logger.info(f"✅ 检测到豆包API密钥格式")
                return 'doubao'
        
        # Llama API密钥格式：LLM|数字|字符串
        if key.startswith("LLM|"):
            logger.info(f"✅ 检测到Llama API密钥格式")
            return 'llama'
        # Qwen密钥格式：sk-xxx
        elif key.startswith("sk-"):
            logger.info(f"✅ 检测到Qwen API密钥格式")
            return 'qwen'
        # OpenAI密钥格式：sk-proj-xxx
        elif key.startswith("sk-proj-"):
            logger.info(f"✅ 检测到OpenAI API密钥格式")
            return 'openai'
        else:
            logger.warning(f"⚠️ 无法识别的API密钥格式: {key[:10]}..., 将尝试作为OpenAI密钥")
            return 'openai'
    
    def _get_test_model(self) -> str:
        """获取用于健康检查的测试模型"""
        if self._client_type == 'doubao':
            # 对于豆包，使用轻量级模型进行测试
            return "doubao-lite-4k"
        elif self._client_type == 'llama':
            # 对于Llama，使用最轻量级的模型进行测试
            return "Llama-3.3-8B-Instruct"
        elif self._client_type == 'qwen':
            # 对于Qwen，使用turbo模型进行快速测试
            return "qwen-turbo"
        else:
            # 对于其他类型，使用默认模型
            return "gpt-3.5-turbo"
    
    @with_retry(RetryConfig(max_retries=2, base_delay=1.0))
    async def _health_check(self) -> bool:
        """检查客户端健康状态"""
        if self._is_closing:
            return False
            
        current_time = time.time()
        
        # 如果最近检查过且状态健康，直接返回
        if (current_time - self._last_health_check < 30 and 
            self._is_healthy and 
            self._retry_count < 3):
            return True
        
        # 如果重试次数过多，暂时标记为不健康
        if self._retry_count >= self._max_retries:
            logger.warning(f"⚠️ {self._client_type}客户端重试次数过多，暂时跳过")
            return False
        
        try:
            # 确保客户端已初始化
            client = self._get_client()
            
            # 如果是Mock客户端，直接返回False
            if isinstance(client, MockHTTPClient):
                self._is_healthy = False
                logger.debug("❌ Mock客户端无法通过健康检查")
                return False
            
            # 获取适合的测试模型
            test_model = self._get_test_model()
            
            # 进行简单的API调用测试
            logger.debug(f"🔍 开始{self._client_type}客户端健康检查 (模型: {test_model})")
            
            response = await client.chat.completions.create(
                model=test_model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1,
                timeout=self._connection_timeout
            )
            
            # 检查响应是否有效
            if response and hasattr(response, 'choices') and len(response.choices) > 0:
                self._is_healthy = True
                self._retry_count = 0
                self._last_health_check = current_time
                logger.debug(f"✅ {self._client_type}客户端健康检查通过")
                return True
            else:
                raise ValueError("API响应格式无效")
            
        except Exception as e:
            self._is_healthy = False
            self._retry_count += 1
            self._last_health_check = current_time
            
            # 使用统一错误处理
            error_info = log_error(e, {
                "client_type": self._client_type,
                "base_url": self.base_url,
                "retry_count": self._retry_count
            })
            
            # 根据错误类型提供更详细的日志和处理策略
            error_msg = str(e).lower()
            if "api key" in error_msg or "unauthorized" in error_msg or "401" in error_msg:
                logger.error(f"🔑 {self._client_type}客户端API密钥无效: {e}")
                # API密钥错误通常是致命的，增加重试计数
                self._retry_count = self._max_retries
            elif "timeout" in error_msg or "connection" in error_msg or "network" in error_msg:
                logger.warning(f"🌐 {self._client_type}客户端网络连接问题 (重试次数: {self._retry_count}): {e}")
            elif "rate limit" in error_msg or "quota" in error_msg or "429" in error_msg:
                logger.warning(f"⏱️ {self._client_type}客户端达到速率限制 (重试次数: {self._retry_count}): {e}")
                # 速率限制时等待更长时间
                await asyncio.sleep(min(2 ** self._retry_count, 60))
            elif "model" in error_msg or "not found" in error_msg or "404" in error_msg:
                logger.error(f"🤖 {self._client_type}客户端模型不可用: {e}")
            else:
                logger.warning(f"❌ {self._client_type}客户端健康检查失败 (重试次数: {self._retry_count}): {e}")
            
            return False
        
    def _get_client(self):
        """延迟初始化真实的客户端"""
        if self._client is None:
            if self.api_key:
                try:
                    # 使用httpx替代OpenAI客户端
                    import httpx
                    
                    # 验证并获取API密钥类型
                    self._client_type = self._validate_api_key(self.api_key)
                    
                    if self._client_type == 'doubao':
                        # 豆包API使用火山引擎端点
                        doubao_base_url = self.base_url or "https://ark.cn-beijing.volces.com/api/v3"
                        
                        # 豆包使用自定义header进行认证 - 修复参数问题
                        doubao_attempts = [
                            # 尝试1: 仅基础必需参数，完全清理所有可能有问题的参数
                            {
                                "api_key": str(self.api_key).strip().replace('"', '').replace("'", ""),
                                "base_url": doubao_base_url,
                                "timeout": 30.0
                            }
                        ]
                        
                        client_created = False
                        for attempt_num, doubao_kwargs in enumerate(doubao_attempts, 1):
                            try:
                                logger.debug(f"尝试初始化豆包客户端 (方案{attempt_num}): {list(doubao_kwargs.keys())}")
                                if AsyncOpenAI is None:
                                    raise ImportError("OpenAI库未安装")
                                
                                # 确保所有参数都是干净的，没有额外引号
                                clean_kwargs = {}
                                clean_kwargs["api_key"] = str(doubao_kwargs["api_key"]).strip()
                                clean_kwargs["base_url"] = str(doubao_kwargs["base_url"]).strip()
                                clean_kwargs["timeout"] = doubao_kwargs["timeout"]
                                
                                self._client = AsyncOpenAI(**clean_kwargs)
                                client_created = True
                                logger.info(f"✅ 豆包客户端初始化成功 (方案{attempt_num})")
                                break
                            except TypeError as e:
                                logger.warning(f"⚠️ 豆包客户端初始化方案{attempt_num}失败: {e}")
                                if attempt_num < len(doubao_attempts):
                                    continue  # 尝试下一个方案
                                else:
                                    raise  # 最后一次尝试也失败则抛出
                        
                        if not client_created:
                            raise RuntimeError("所有豆包客户端初始化方案都失败")
                        logger.info(f"✅ 成功初始化豆包客户端 (base_url: {doubao_base_url})")
                    elif self._client_type == 'llama':
                        # Llama API修复参数传递
                        base_url = self.base_url or "https://api.llama-api.com/v1"
                        
                        # 使用最小参数集避免兼容性问题
                        client_attempts = [
                            # 仅基础参数，清理API密钥格式
                            {
                                "api_key": str(self.api_key).strip().replace('"', '').replace("'", ""),
                                "base_url": base_url,
                                "timeout": 30.0
                            }
                        ]
                        
                        client_created = False
                        for attempt_num, client_kwargs in enumerate(client_attempts, 1):
                            try:
                                logger.debug(f"尝试初始化Llama客户端 (方案{attempt_num}): {list(client_kwargs.keys())}")
                                if AsyncOpenAI is None:
                                    raise ImportError("OpenAI库未安装")
                                
                                # 确保参数干净
                                clean_kwargs = {}
                                clean_kwargs["api_key"] = str(client_kwargs["api_key"]).strip()
                                clean_kwargs["base_url"] = str(client_kwargs["base_url"]).strip()
                                clean_kwargs["timeout"] = client_kwargs["timeout"]
                                
                                self._client = AsyncOpenAI(**clean_kwargs)
                                client_created = True
                                logger.info(f"✅ Llama客户端初始化成功 (方案{attempt_num})")
                                break
                            except TypeError as e:
                                logger.warning(f"⚠️ Llama客户端初始化方案{attempt_num}失败: {e}")
                                if attempt_num < len(client_attempts):
                                    continue  # 尝试下一个方案
                                else:
                                    raise  # 最后一次尝试也失败则抛出
                        
                        if not client_created:
                            raise RuntimeError("所有Llama客户端初始化方案都失败")
                        logger.info(f"✅ 成功初始化Llama客户端 (base_url: {base_url})")
                    elif self._client_type == 'qwen':
                        # Qwen API修复参数传递
                        qwen_base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
                        qwen_attempts = [
                            # 仅使用必需参数，清理API密钥格式
                            {
                                "api_key": str(self.api_key).strip().replace('"', '').replace("'", ""),
                                "base_url": qwen_base_url,
                                "timeout": 30.0
                            }
                        ]
                        
                        client_created = False
                        for attempt_num, qwen_kwargs in enumerate(qwen_attempts, 1):
                            try:
                                logger.debug(f"尝试初始化Qwen客户端 (方案{attempt_num}): {list(qwen_kwargs.keys())}")
                                if AsyncOpenAI is None:
                                    raise ImportError("OpenAI库未安装")
                                
                                # 确保参数干净
                                clean_kwargs = {}
                                clean_kwargs["api_key"] = str(qwen_kwargs["api_key"]).strip()
                                clean_kwargs["base_url"] = str(qwen_kwargs["base_url"]).strip()
                                clean_kwargs["timeout"] = qwen_kwargs["timeout"]
                                
                                self._client = AsyncOpenAI(**clean_kwargs)
                                client_created = True
                                logger.info(f"✅ Qwen客户端初始化成功 (方案{attempt_num})")
                                break
                            except TypeError as e:
                                logger.warning(f"⚠️ Qwen客户端初始化方案{attempt_num}失败: {e}")
                                if attempt_num < len(qwen_attempts):
                                    continue  # 尝试下一个方案
                                else:
                                    raise  # 最后一次尝试也失败则抛出
                        
                        if not client_created:
                            raise RuntimeError("所有Qwen客户端初始化方案都失败")
                    else:
                        # 标准OpenAI API（已废弃，但保留兼容性）
                        # 使用最小参数集避免兼容性问题
                        openai_kwargs = {
                            "api_key": self.api_key
                        }
                        
                        # 只在需要时添加超时
                        try:
                            if AsyncOpenAI is None:
                                raise ImportError("OpenAI库未安装")
                            self._client = AsyncOpenAI(**openai_kwargs)
                        except TypeError as e:
                            logger.warning(f"⚠️ OpenAI客户端初始化失败: {e}")
                            # 如果初始化失败，降级到Mock客户端
                            self._client = MockHTTPClient()
                            self._client_type = 'mock'
                            return self._client
                        logger.info("✅ 成功初始化OpenAI客户端")
                    return self._client
                except Exception as e:
                    logger.error(f"❌ 客户端初始化失败: {e}")
                    self._client = MockHTTPClient()
                    self._client_type = 'mock'
            else:
                logger.error("❌ 无有效的API密钥，使用Mock客户端")
                self._client = MockHTTPClient()
                self._client_type = 'mock'
                
        return self._client
    
    @property 
    def chat(self):
        return self._get_client().chat
        
    @property
    def audio(self):
        return self._get_client().audio
    
    async def aclose(self):
        """异步关闭客户端"""
        if self._is_closing:
            return
            
        self._is_closing = True
        
        if self._client:
            try:
                # 检查客户端类型并安全关闭
                if hasattr(self._client, 'close'):
                    if asyncio.iscoroutinefunction(self._client.close):
                        await self._client.close()
                    else:
                        self._client.close()
                elif hasattr(self._client, 'aclose'):
                    await self._client.aclose()
                
                logger.debug(f"🔒 {self._client_type}客户端已关闭")
            except Exception as e:
                logger.warning(f"⚠️ 关闭{self._client_type}客户端时出错: {e}")
            finally:
                self._client = None
                self._client_type = None
                self._is_healthy = False
                
        # 从全局注册表中移除
        try:
            _client_registry.discard(self)
        except Exception:
            pass  # WeakSet可能已经自动清理
        
    def __getattr__(self, name):
        """代理所有其他属性到真实客户端"""
        return getattr(self._get_client(), name)


class MockHTTPClient:
    """Mock HTTP客户端，用于启动时的占位"""
    
    def __init__(self):
        self.chat = MockChat()
        self.audio = MockAudio()


class MockChat:
    def __init__(self):
        self.completions = MockCompletions()


class MockCompletions:
    async def create(self, **kwargs):
        raise Exception("HTTP客户端未正确初始化，请检查API密钥和网络连接")


class MockAudio:
    def __init__(self):
        self.transcriptions = MockTranscriptions()
        self.speech = MockSpeech()


class MockTranscriptions:
    async def create(self, **kwargs):
        raise Exception("语音识别服务未正确初始化，请使用本地Whisper服务")


class MockSpeech:
    async def create(self, **kwargs):
        raise Exception("语音合成服务未正确初始化，请使用本地TTS服务")


async def safe_chat_completion(client, **kwargs):
    """
    安全的聊天补全调用
    支持自动重试和错误处理
    """
    max_retries = 3
    retry_delay = 1.0
    
    for attempt in range(max_retries):
        try:
            # 如果是LazyHTTPClient，先进行健康检查
            if isinstance(client, LazyHTTPClient):
                await client._health_check()
            
            response = await client.chat.completions.create(**kwargs)
            return response
        except Exception as e:
            logger.warning(f"聊天补全调用失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay * (2 ** attempt))  # 指数退避
            else:
                logger.error(f"聊天补全调用最终失败: {e}")
                raise


async def safe_transcription(client, **kwargs):
    """
    安全的转录调用
    支持自动重试和错误处理
    """
    max_retries = 3
    retry_delay = 1.0
    
    for attempt in range(max_retries):
        try:
            # 如果是LazyHTTPClient，先进行健康检查
            if isinstance(client, LazyHTTPClient):
                await client._health_check()
            
            response = await client.audio.transcriptions.create(**kwargs)
            return response
        except Exception as e:
            logger.warning(f"转录调用失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay * (2 ** attempt))  # 指数退避
            else:
                logger.error(f"转录调用最终失败: {e}")
                raise


async def safe_speech_synthesis(client, **kwargs):
    """
    安全的语音合成调用
    支持自动重试和错误处理
    """
    max_retries = 3
    retry_delay = 1.0
    
    for attempt in range(max_retries):
        try:
            # 如果是LazyHTTPClient，先进行健康检查
            if isinstance(client, LazyHTTPClient):
                await client._health_check()
            
            response = await client.audio.speech.create(**kwargs)
            return response
        except Exception as e:
            logger.warning(f"语音合成调用失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay * (2 ** attempt))  # 指数退避
            else:
                logger.error(f"语音合成调用最终失败: {e}")
                raise 


# 移除所有HuggingFace相关实现，只保留OpenAI兼容接口


class ClientManager:
    """客户端管理器
    负责管理多个客户端实例和自动切换
    """
    
    def __init__(self):
        self._clients = {}
        self._current_client = None
        self._fallback_enabled = True
        self._prefer_doubao = True  # 优先使用豆包
        self._prefer_qwen = False   # Qwen作为备用
        
    def register_client(self, name: str, client: LazyHTTPClient):
        """注册客户端"""
        self._clients[name] = client
        if self._current_client is None:
            self._current_client = name
    
    def set_preferences(self, prefer_doubao: bool = True, prefer_qwen: bool = False, fallback_enabled: bool = True):
        """设置客户端偏好 - 现在支持豆包优先"""
        self._prefer_doubao = prefer_doubao
        self._prefer_qwen = prefer_qwen and not prefer_doubao  # 如果豆包优先，则不优先Qwen
        self._fallback_enabled = fallback_enabled
    
    async def get_healthy_client(self, exclude_current: bool = False, provider_type: Optional[str] = None):
        """
        获取健康的客户端
        
        Args:
            exclude_current: 是否排除当前客户端
            provider_type: 指定提供商类型 ('llama', 'qwen' 或 'openai')，如果不指定则根据偏好选择
        """
        # 如果没有注册的客户端，返回None
        if not self._clients:
            logger.error("❌ 没有注册的客户端")
            return None
        
        # 如果指定了提供商类型，优先返回该类型的健康客户端
        if provider_type:
            for name, client in self._clients.items():
                # 先初始化客户端以确定类型
                client._get_client()
                if client._client_type == provider_type:
                    if await client._health_check():
                        return client
            logger.warning(f"⚠️ 没有健康的{provider_type}客户端")
            return None
        
        # 根据偏好设置决定优先顺序 - 豆包优先架构
        if self._prefer_doubao:
            # 1. 优先尝试豆包客户端
            for name, client in self._clients.items():
                # 先初始化客户端以确定类型
                client._get_client()
                if client._client_type == 'doubao' and (not exclude_current or name != self._current_client):
                    if await client._health_check():
                        if name != self._current_client:
                            logger.info(f"🔄 切换到豆包客户端: {name}")
                            self._current_client = name
                        return client
            
            # 2. 如果豆包不可用，尝试Qwen
            if self._fallback_enabled:
                for name, client in self._clients.items():
                    # 先初始化客户端以确定类型
                    client._get_client()
                    if client._client_type == 'qwen':
                        if await client._health_check():
                            logger.info(f"⚠️ 豆包不可用，切换到Qwen备份客户端: {name}")
                            self._current_client = name
                            return client
            
            # 3. 最后尝试Llama作为最终备用
            if self._fallback_enabled:
                for name, client in self._clients.items():
                    # 先初始化客户端以确定类型
                    client._get_client()
                    if client._client_type == 'llama':
                        if await client._health_check():
                            logger.info(f"⚠️ 豆包和Qwen都不可用，切换到Llama最终备份客户端: {name}")
                            self._current_client = name
                            return client
        elif self._prefer_qwen:
            # 如果偏好Qwen（向后兼容）
            # 优先尝试Qwen客户端
            for name, client in self._clients.items():
                # 先初始化客户端以确定类型
                client._get_client()
                if client._client_type == 'qwen' and (not exclude_current or name != self._current_client):
                    if await client._health_check():
                        if name != self._current_client:
                            logger.info(f"🔄 切换到Qwen客户端: {name}")
                            self._current_client = name
                        return client
            
            # 如果Qwen不可用且启用了备份，尝试Llama
            if self._fallback_enabled:
                for name, client in self._clients.items():
                    # 先初始化客户端以确定类型
                    client._get_client()
                    if client._client_type == 'llama':
                        if await client._health_check():
                            logger.info(f"⚠️ Qwen不可用，切换到Llama备份客户端: {name}")
                            self._current_client = name
                            return client
        else:
            # 优先尝试Llama客户端
            for name, client in self._clients.items():
                # 先初始化客户端以确定类型
                client._get_client()
                if client._client_type == 'llama' and (not exclude_current or name != self._current_client):
                    if await client._health_check():
                        if name != self._current_client:
                            logger.info(f"🔄 切换到Llama客户端: {name}")
                            self._current_client = name
                        return client
            
            # 如果Llama不可用，尝试Qwen
            for name, client in self._clients.items():
                # 先初始化客户端以确定类型
                client._get_client()
                if client._client_type == 'qwen':
                    if await client._health_check():
                        logger.info(f"⚠️ Llama不可用，切换到Qwen客户端: {name}")
                        self._current_client = name
                        return client
        
        logger.error("❌ 没有可用的健康客户端")
        return None
    
    def get_client_type(self, client) -> str:
        """获取客户端类型"""
        if hasattr(client, '_client_type'):
            return client._client_type
        return "unknown"
    
    def get_client_status(self) -> Dict[str, Any]:
        """获取所有客户端状态"""
        status = {
            "current_client": self._current_client,
            "fallback_enabled": self._fallback_enabled,
            "prefer_qwen": self._prefer_qwen,
            "clients": {},
            # 保留旧字段用于兼容性
            "prefer_llama": False
        }
        
        for name, client in self._clients.items():
            status["clients"][name] = {
                "type": client._client_type,
                "healthy": client._is_healthy,
                "last_check": datetime.fromtimestamp(client._last_health_check).isoformat() if client._last_health_check > 0 else None,
                "retry_count": client._retry_count
            }
        
        return status


# 全局客户端管理器实例
client_manager = ClientManager()


def get_client_manager() -> ClientManager:
    """获取全局客户端管理器"""
    return client_manager


def initialize_clients():
    """初始化所有配置的客户端 - 豆包优先三模型架构"""
    from .config import VITAConfig as config
    
    # 设置客户端管理器偏好 - 豆包优先
    client_manager.set_preferences(
        prefer_doubao=getattr(config, 'PREFER_DOUBAO', True),
        prefer_qwen=config.PREFER_QWEN and not getattr(config, 'PREFER_DOUBAO', True),
        fallback_enabled=config.USE_LLAMA_FALLBACK
    )
    
    # 1. 尝试初始化豆包客户端（首选）
    try:
        doubao_key = config.get_doubao_key()
        if doubao_key:  # 只有当密钥不为空时才尝试注册
            doubao_base_url = config.get_doubao_base_url()
            doubao_client = create_http_client(doubao_key, doubao_base_url)
            client_manager.register_client("doubao", doubao_client)
            logger.info("✅ 豆包客户端已注册")
        else:
            logger.warning("⚠️ 豆包API密钥为空，跳过豆包客户端注册")
    except Exception as e:
        logger.warning(f"⚠️ 豆包客户端注册失败: {e}")
    
    # 2. 尝试初始化Qwen客户端（备用）
    try:
        qwen_key = config.get_qwen_key()
        if qwen_key:  # 只有当密钥不为空时才尝试注册
            qwen_client = create_http_client(qwen_key)
            client_manager.register_client("qwen", qwen_client)
            logger.info("✅ Qwen客户端已注册")
        else:
            logger.warning("⚠️ Qwen API密钥为空，跳过Qwen客户端注册")
    except Exception as e:
        logger.warning(f"⚠️ Qwen客户端注册失败: {e}")
    
    # 3. 尝试初始化Llama客户端（最终备用）
    try:
        llama_key = config.get_llama_key()
        if llama_key:  # 只有当密钥不为空时才尝试注册
            llama_base_url = config.get_llama_base_url()
            llama_client = create_http_client(llama_key, llama_base_url)
            client_manager.register_client("llama", llama_client)
            logger.info("✅ Llama客户端已注册")
        else:
            logger.warning("⚠️ Llama API密钥为空，跳过Llama客户端注册")
    except Exception as e:
        logger.warning(f"⚠️ Llama客户端注册失败: {e}")
    
    # 检查是否至少有一个客户端
    if not client_manager._clients:
        logger.error("❌ 没有成功注册任何客户端，请检查API密钥配置")
        logger.info("💡 提示：请设置至少一个有效的API密钥：")
        logger.info("   - DOUBAO_API_KEY: 豆包API密钥")
        logger.info("   - QWEN_API_KEY: Qwen API密钥")
        logger.info("   - LLAMA_API_KEY: Llama API密钥")
        raise ValueError("❌ 没有可用的API客户端")
    
    logger.info("🔧 豆包优先三模型客户端管理器初始化完成")