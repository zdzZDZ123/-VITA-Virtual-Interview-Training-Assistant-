"""
LLM 聊天封装模块
"""
import logging
import time
from typing import List, Dict, Optional, Any, AsyncGenerator, Tuple
from core.prompts import SYSTEM_PROMPT, FEEDBACK_PROMPT, get_interview_prompt
from .config import config
from core.qwen_llama_client import create_http_client, safe_chat_completion, initialize_clients, get_client_manager
from .performance_monitor import get_performance_monitor, PerformanceContext, async_timeit
from core.error_handler import with_retry, RetryConfig, handle_errors, ErrorCategory
from .health_monitor import record_request_metrics
from core.cache_manager import get_cache, cache_key_for_chat
import asyncio
import json
import uuid
from datetime import datetime, timedelta
import threading
import weakref

logger = logging.getLogger(__name__)

# 预设面试题库 - 作为API不可用时的回退
FALLBACK_QUESTIONS = {
    "technical": [
        "请解释一下 JavaScript 中的事件循环 (event loop) 。",
        "什么是 React 的虚拟DOM？它如何提高性能？",
        "请描述 HTTP 和 HTTPS 的区别，以及 HTTPS 的工作原理。",
        "什么是响应式设计？请说明其核心原则。",
        "请解释 TypeScript 相比 JavaScript 的优势。",
        "什么是 RESTful API？请说明其设计原则。",
        "请描述前端性能优化的常见方法。",
        "什么是 Git 的分支策略？请说明常见的工作流程。",
        "请解释 CSS 盒模型的概念。",
        "什么是异步编程？请比较 Promise 和 async/await。"
    ],
    "behavioral": [
        "请描述一个你遇到的最具挑战性的项目，以及你是如何解决问题的。",
        "谈谈你在团队合作中遇到的困难，以及你是如何处理的。",
        "描述一次你必须在紧迫的截止日期前完成工作的经历。",
        "请举例说明你如何处理与同事意见不合的情况。",
        "谈谈你最引以为豪的一个工作成就。",
        "描述一次你从失败中学到重要经验的经历。",
        "请说明你如何平衡工作和个人生活。",
        "谈谈你如何持续学习和提升自己的技能。",
        "描述一次你需要快速适应新技术或新环境的经历。",
        "请举例说明你如何给团队成员提供帮助或指导。"
    ],
    "situational": [
        "如果你发现代码中有一个严重的安全漏洞，但修复它可能影响项目进度，你会怎么处理？",
        "假设你的直接上级给你分配了一个你认为不合理的任务，你会如何应对？",
        "如果客户要求在很短时间内交付一个复杂功能，你会如何规划和执行？",
        "假设你发现团队成员的代码质量不符合标准，你会如何处理？",
        "如果在项目进行中发现需求有重大变化，你会采取什么措施？",
        "假设你需要在多个紧急任务之间做选择，你会如何确定优先级？",
        "如果你对某个技术决策有不同意见，但团队已经决定，你会怎么做？",
        "假设项目出现严重bug影响用户体验，你会如何快速响应？",
        "如果你需要向非技术人员解释复杂的技术问题，你会采用什么方法？",
        "假设你发现现有系统架构存在性能瓶颈，你会如何提出改进建议？"
    ]
}

class InterviewSession:
    """面试会话管理"""
    def __init__(self, session_id: str, job_description: str, interview_type: str):
        self.session_id = session_id
        self.job_description = job_description
        self.interview_type = interview_type
        self.questions_asked = []
        self.answers = []
        self.current_question_index = 0
        self.created_at = datetime.now()
        self.last_activity = datetime.now()  # 添加最后活动时间
        self.using_fallback = False
        
    def add_qa_pair(self, question: str, answer: Optional[str] = None):
        """添加问答对"""
        self.last_activity = datetime.now()  # 更新活动时间
        if answer is None:
            # 只添加问题
            self.questions_asked.append(question)
        else:
            # 添加答案到对应问题
            if len(self.answers) < len(self.questions_asked):
                self.answers.append(answer)

class ChatService:
    """封装 LLM 调用逻辑，支持智能模型选择、Qwen优先架构和优化配置"""
    
    def __init__(self):
        try:
            # 初始化客户端
            initialize_clients()
            
            # 使用客户端管理器获取客户端
            self.client_manager = get_client_manager()
            self.performance_monitor = get_performance_monitor()
            
            # 使用线程安全的会话管理
            self._sessions_lock = threading.RLock()
            self.sessions: Dict[str, InterviewSession] = {}
            self.fallback_questions = FALLBACK_QUESTIONS
            
            # 会话清理配置
            self.max_sessions = 1000  # 最大会话数
            self.session_timeout_hours = 24  # 会话超时时间（小时）
            self.cleanup_interval = 3600  # 清理间隔（秒）
            self._last_cleanup = time.time()
            
            # 启动定期清理任务
            self._cleanup_task = None
            self._start_cleanup_task()
            
            logger.info("ChatService 初始化成功 (Qwen优先架构)")
        except Exception as e:
            logger.error(f"ChatService 初始化失败: {e}")
            raise
    
    def _start_cleanup_task(self):
        """启动定期清理任务"""
        try:
            async def cleanup_loop():
                while True:
                    try:
                        await asyncio.sleep(self.cleanup_interval)
                        await self._cleanup_expired_sessions()
                    except Exception as e:
                        logger.warning(f"会话清理任务异常: {e}")
            
            # 检查是否有事件循环
            try:
                loop = asyncio.get_running_loop()
                self._cleanup_task = asyncio.create_task(cleanup_loop())
                logger.info("✅ 会话清理任务已启动")
            except RuntimeError:
                # 没有运行的事件循环，稍后启动
                logger.debug("⏳ 等待事件循环启动后再启动清理任务")
        except Exception as e:
            logger.warning(f"启动清理任务失败: {e}")
    
    async def _cleanup_expired_sessions(self):
        """清理过期会话"""
        try:
            current_time = datetime.now()
            timeout_delta = timedelta(hours=self.session_timeout_hours)
            expired_sessions = []
            
            with self._sessions_lock:
                # 找到过期会话
                for session_id, session in list(self.sessions.items()):
                    if current_time - session.last_activity > timeout_delta:
                        expired_sessions.append(session_id)
                
                # 删除过期会话
                for session_id in expired_sessions:
                    del self.sessions[session_id]
                
                # 如果会话数量仍然过多，删除最旧的会话
                if len(self.sessions) > self.max_sessions:
                    # 按最后活动时间排序，删除最旧的
                    sessions_by_activity = sorted(
                        self.sessions.items(),
                        key=lambda x: x[1].last_activity
                    )
                    
                    excess_count = len(self.sessions) - self.max_sessions
                    for i in range(excess_count):
                        session_id = sessions_by_activity[i][0]
                        del self.sessions[session_id]
                        expired_sessions.append(session_id)
            
            if expired_sessions:
                logger.info(f"🧹 清理了 {len(expired_sessions)} 个过期/过多会话")
            
            self._last_cleanup = time.time()
            
        except Exception as e:
            logger.error(f"清理过期会话失败: {e}")
    
    def _ensure_cleanup_task(self):
        """确保清理任务正在运行"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._start_cleanup_task()
    
    @async_timeit(metric_name="llm.ask", log_slow_threshold=2.0)
    async def ask_llm(
        self, 
        messages: List[Dict[str, str]], 
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 256,
        task_type: str = "chat"
    ) -> str:
        """
        调用 LLM 获取回复，智能选择最佳模型，支持Qwen优先架构自动切换
        
        Args:
            messages: 对话历史，格式 [{"role": "user|assistant|system", "content": "..."}]
            model: 指定模型名称，如果未提供则根据任务类型自动选择
            temperature: 随机性控制
            max_tokens: 最大token数
            task_type: 任务类型，用于自动模型选择
            
        Returns:
            LLM 生成的回复内容
        """
        try:
            # 首先尝试使用Qwen客户端（现在是主要提供商）
            client = await self.client_manager.get_healthy_client(provider_type='qwen')
            
            if client:
                # 使用Qwen模型
                selected_model = model or config.get_model_for_provider('qwen', task_type)
                logger.info(f"使用Qwen的{selected_model}模型处理{task_type}任务")
                
                try:
                    async with PerformanceContext(
                        self.performance_monitor,
                        provider='qwen',
                        function_type=task_type
                    ):
                        response = await safe_chat_completion(
                            client,
                            model=selected_model,
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                        )
                        return response.choices[0].message.content.strip()
                except Exception as e:
                    logger.error(f"Qwen调用失败: {str(e)}")
                    # 如果Qwen调用失败，继续尝试Llama
                    if not (config.USE_LLAMA_FALLBACK and config.ENABLE_AUTO_SWITCH):
                        raise
            
            # 如果Qwen不可用或调用失败，且启用了备份，尝试Llama
            if config.USE_LLAMA_FALLBACK and config.ENABLE_AUTO_SWITCH:
                logger.info("尝试使用Llama备份客户端")
                fallback_client = await self.client_manager.get_healthy_client(provider_type='llama')
                
                if fallback_client:
                    # 使用Llama模型
                    selected_model = model or config.get_model_for_provider('llama', task_type)
                    logger.info(f"使用Llama的{selected_model}模型处理{task_type}任务")
                    
                    async with PerformanceContext(
                        self.performance_monitor,
                        provider='llama',
                        function_type=task_type
                    ):
                        response = await safe_chat_completion(
                            fallback_client,
                            model=selected_model,
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                        )
                        return response.choices[0].message.content.strip()
            
            # 如果都失败了
            raise Exception("没有可用的LLM客户端")
            
        except Exception as e:
            logger.error(f"LLM调用失败: {str(e)}")
            raise Exception(f"LLM调用失败: {str(e)}")

    
    async def generate_interview_question(
        self, 
        job_description: str, 
        interview_type: str = "technical",
        previous_qa: List[Tuple[str, str]] = None,
        question_number: int = 1,
        conversation_history: List[Dict[str, str]] = None  # 向后兼容的参数
    ) -> str:
        """
        生成面试问题
        优先使用AI模型，失败时使用预设问题
        """
        try:
            # 尝试使用AI模型生成问题
            ai_question = await self._generate_ai_question(
                job_description, interview_type, previous_qa, question_number
            )
            if ai_question:
                return ai_question
        except Exception as e:
            logger.warning(f"AI问题生成失败，使用回退问题: {e}")
        
        # 使用预设问题作为回退
        return self._get_fallback_question(interview_type, question_number)
    
    async def _generate_ai_question(
        self,
        job_description: str,
        interview_type: str,
        previous_qa: List[Tuple[str, str]] = None,
        question_number: int = 1
    ) -> Optional[str]:
        """使用AI模型生成问题"""
        try:
            # 优先尝试Qwen，然后尝试Llama
            for provider in ['qwen', 'llama']:
                try:
                    client = await self.client_manager.get_healthy_client(provider_type=provider)
                    if not client:
                        continue
                    
                    model = config.get_model_for_provider(provider, "interview")
                    prompt = get_interview_prompt(
                        job_description, interview_type, previous_qa, question_number
                    )
                    
                    response = await safe_chat_completion(
                        client,
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=500,
                        temperature=0.7
                    )
                    
                    if response and response.choices:
                        question = response.choices[0].message.content.strip()
                        logger.info(f"✅ 使用{provider}模型生成问题成功")
                        return question
                        
                except Exception as e:
                    logger.warning(f"⚠️ {provider}模型生成问题失败: {e}")
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"❌ AI问题生成失败: {e}")
            return None
    
    def _get_fallback_question(self, interview_type: str, question_number: int) -> str:
        """获取预设回退问题，支持智能选择"""
        questions = self.fallback_questions.get(interview_type, self.fallback_questions["technical"])
        
        # 循环使用问题，避免超出范围
        index = (question_number - 1) % len(questions)
        question = questions[index]
        
        # 为问题添加变化以避免重复感
        if question_number > len(questions):
            # 当问题数超过预设数量时，添加序号变化
            cycle_num = (question_number - 1) // len(questions) + 1
            if cycle_num > 1:
                question = f"[深入] {question}"
        
        logger.info(f"📝 使用本地问题库 ({interview_type}, #{question_number}): {question[:50]}...")
        return question
    
    async def start_interview_session(
        self, 
        job_description: str, 
        interview_type: str = "technical"
    ) -> Dict[str, Any]:
        """开始面试会话"""
        # 确保清理任务在运行
        self._ensure_cleanup_task()
        
        session_id = str(uuid.uuid4())
        
        # 创建会话
        session = InterviewSession(session_id, job_description, interview_type)
        
        with self._sessions_lock:
            self.sessions[session_id] = session
        
        # 生成第一个问题
        first_question = await self.generate_interview_question(
            job_description, interview_type, question_number=1
        )
        
        session.add_qa_pair(first_question)
        
        logger.info(f"🚀 面试会话已创建: {session_id}")
        
        return {
            "session_id": session_id,
            "first_question": first_question,
            "interview_type": interview_type,
            "created_at": session.created_at.isoformat()
        }
    
    async def __REMOVED_API_KEY__(
        self, 
        session_id: str, 
        answer: str
    ) -> Dict[str, Any]:
        """处理答案并生成下一个问题"""
        with self._sessions_lock:
            if session_id not in self.sessions:
                raise ValueError("会话不存在")
            
            session = self.sessions[session_id]
        
        # 记录答案
        session.add_qa_pair(None, answer)
        session.current_question_index += 1
        
        # 生成下一个问题
        previous_qa = list(zip(session.questions_asked, session.answers))
        next_question = await self.generate_interview_question(
            session.job_description,
            session.interview_type,
            previous_qa,
            session.current_question_index + 1
        )
        
        session.add_qa_pair(next_question)
        
        return {
            "question": next_question,
            "question_number": session.current_question_index + 1,
            "total_questions": len(session.questions_asked)
        }
    
    def get_session(self, session_id: str) -> Optional[InterviewSession]:
        """获取会话信息"""
        with self._sessions_lock:
            return self.sessions.get(session_id)
    
    def end_session(self, session_id: str) -> Dict[str, Any]:
        """结束会话并生成总结"""
        with self._sessions_lock:
            if session_id not in self.sessions:
                raise ValueError("会话不存在")
            
            session = self.sessions[session_id]
            
            # 简单的总结
            summary = {
                "session_id": session_id,
                "interview_type": session.interview_type,
                "questions_count": len(session.questions_asked),
                "answers_count": len(session.answers),
                "duration": (datetime.now() - session.created_at).total_seconds(),
                "completed": len(session.answers) >= len(session.questions_asked)
            }
            
            # 清理会话
            del self.sessions[session_id]
        
        return summary
    
    def get_session_stats(self) -> Dict[str, Any]:
        """获取会话统计信息"""
        with self._sessions_lock:
            return {
                "total_sessions": len(self.sessions),
                "max_sessions": self.max_sessions,
                "cleanup_interval_seconds": self.cleanup_interval,
                "session_timeout_hours": self.session_timeout_hours,
                "last_cleanup": self._last_cleanup
            }

    async def generate_feedback_report(
        self, 
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """
        生成面试反馈报告，使用最强模型确保分析质量
        
        Args:
            conversation_history: 完整的对话历史
            
        Returns:
            结构化的反馈报告
        """
        # 将对话历史转换为文本
        transcript = "\n".join([
            f"{'面试官' if h['role'] == 'assistant' else '候选人'}: {h['content']}" 
            for h in conversation_history if h['role'] in ['user', 'assistant']
        ])
        
        messages = [
            {"role": "system", "content": FEEDBACK_PROMPT},
            {"role": "user", "content": f"面试记录：\n{transcript}"}
        ]
        
        # 使用analysis任务类型，自动选择最强模型进行深度分析
        return await self.ask_llm(
            messages, 
            temperature=0.5, 
            max_tokens=1024,
            task_type="analysis"
        )
    
    async def cleanup(self):
        """清理资源"""
        try:
            # 取消清理任务
            if self._cleanup_task and not self._cleanup_task.done():
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            
            # 清理所有会话
            with self._sessions_lock:
                self.sessions.clear()
            
            logger.info("✅ ChatService资源已清理")
            
        except Exception as e:
            logger.warning(f"⚠️ ChatService清理时出现警告: {e}")

@with_retry(RetryConfig(max_retries=3, base_delay=1.0))
@handle_errors(category=ErrorCategory.API)
async def chat_completion(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    stream: bool = False
) -> Dict[str, Any]:
    """统一的聊天完成接口"""
    start_time = time.time()
    success = False
    
    try:
        # 生成缓存键
        cache_key = cache_key_for_chat(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # 尝试从缓存获取响应（仅对非流式请求）
        if not stream:
            cache = get_cache("chat")
            cached_response = cache.get(cache_key)
            if cached_response:
                success = True
                return cached_response
        
        # 获取健康的客户端
        client = await get_healthy_client()
        if not client:
            raise Exception("没有可用的健康客户端")
        
        # 如果没有指定模型，使用默认模型
        if not model:
            model = client.get_default_model()
        
        # 调用聊天完成
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )
        
        success = True
        
        if stream:
            return response
        else:
            result = {
                "content": response.choices[0].message.content,
                "model": response.model,
                "usage": response.usage.dict() if response.usage else None
            }
            
            # 缓存响应
            cache = get_cache("chat")
            cache.set(cache_key, result)
            
            return result
            
    except Exception as e:
        logger.error(f"聊天完成失败: {e}")
        raise e
    finally:
        # 记录请求指标
        response_time = time.time() - start_time
        record_request_metrics(response_time, success)

# 全局单例
chat_service = ChatService()

def get_chat_service() -> ChatService:
    """获取聊天服务实例"""
    global chat_service
    return chat_service