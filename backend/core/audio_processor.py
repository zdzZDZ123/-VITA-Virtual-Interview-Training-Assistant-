"""
音频处理模块 - 解决浏览器兼容性问题
使用FFmpeg进行音频格式标准化，确保浏览器完美播放
"""

import asyncio
import tempfile
import os
import subprocess
import logging
from typing import Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class AudioProcessor:
    """音频处理器 - 专门解决浏览器兼容性问题"""
    
    def __init__(self):
        self.ffmpeg_available = self._check_ffmpeg()
        logger.info(f"🎵 AudioProcessor初始化，FFmpeg可用: {self.ffmpeg_available}")
    
    def _check_ffmpeg(self) -> bool:
        """检查FFmpeg是否可用"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                 capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    async def standardize_for_web(
        self, 
        audio_data: bytes, 
        output_format: str = "mp3"
    ) -> Tuple[bytes, str]:
        """
        标准化音频为Web兼容格式
        
        Args:
            audio_data: 原始音频数据
            output_format: 输出格式 (mp3, wav, ogg)
            
        Returns:
            (标准化后的音频数据, MIME类型)
        """
        if not self.ffmpeg_available:
            logger.warning("FFmpeg不可用，返回原始音频")
            return audio_data, "audio/mpeg"
        
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as input_file:
                input_file.write(audio_data)
                input_path = input_file.name
            
            output_path = input_path.replace('.mp3', f'_web.{output_format}')
            
            try:
                # 根据输出格式选择最佳参数
                if output_format == "mp3":
                    # MP3 - 使用Web兼容的编码参数
                    cmd = [
                        'ffmpeg', '-i', input_path,
                        '-acodec', 'libmp3lame',    # 强制使用标准MP3编码器
                        '-ab', '128k',              # 标准比特率
                        '-ar', '22050',             # 标准采样率
                        '-ac', '1',                 # 单声道
                        '-f', 'mp3',                # 强制MP3容器格式
                        '-y',                       # 覆盖输出文件
                        output_path
                    ]
                    mime_type = "audio/mpeg"
                
                elif output_format == "wav":
                    # WAV - 最兼容的格式
                    cmd = [
                        'ffmpeg', '-i', input_path,
                        '-acodec', 'pcm_s16le',     # 16位PCM编码
                        '-ar', '22050',             # 标准采样率
                        '-ac', '1',                 # 单声道
                        '-f', 'wav',                # WAV容器格式
                        '-y',
                        output_path
                    ]
                    mime_type = "audio/wav"
                
                elif output_format == "ogg":
                    # OGG - 开源替代方案
                    cmd = [
                        'ffmpeg', '-i', input_path,
                        '-acodec', 'libvorbis',     # Vorbis编码
                        '-ab', '128k',
                        '-ar', '22050',
                        '-ac', '1',
                        '-f', 'ogg',
                        '-y',
                        output_path
                    ]
                    mime_type = "audio/ogg"
                
                else:
                    raise ValueError(f"不支持的输出格式: {output_format}")
                
                # 执行FFmpeg转换
                logger.debug(f"🔧 执行音频转换: {' '.join(cmd)}")
                result = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await result.communicate()
                
                if result.returncode != 0:
                    logger.error(f"FFmpeg转换失败: {stderr.decode()}")
                    return audio_data, "audio/mpeg"
                
                # 读取转换后的音频
                with open(output_path, 'rb') as f:
                    converted_data = f.read()
                
                logger.info(f"✅ 音频标准化成功: {len(audio_data)}→{len(converted_data)} bytes, 格式: {output_format}")
                return converted_data, mime_type
                
            finally:
                # 清理临时文件
                for path in [input_path, output_path]:
                    if os.path.exists(path):
                        os.unlink(path)
                        
        except Exception as e:
            logger.error(f"❌ 音频标准化失败: {e}")
            return audio_data, "audio/mpeg"
    
    async def create_multi_format_response(self, audio_data: bytes) -> dict:
        """
        创建多格式音频响应
        
        Returns:
            包含多种格式的音频数据字典
        """
        formats = {}
        
        # 生成多种格式
        for fmt in ['mp3', 'wav', 'ogg']:
            try:
                converted_data, mime_type = await self.standardize_for_web(audio_data, fmt)
                formats[fmt] = {
                    'data': converted_data,
                    'mime_type': mime_type,
                    'size': len(converted_data)
                }
            except Exception as e:
                logger.warning(f"生成{fmt}格式失败: {e}")
        
        return formats
    
    def get_browser_preferred_format(self, user_agent: str = "") -> str:
        """根据浏览器返回首选音频格式"""
        user_agent = user_agent.lower()
        
        if 'chrome' in user_agent or 'chromium' in user_agent:
            return 'wav'  # Chrome对WAV支持最好
        elif 'firefox' in user_agent:
            return 'ogg'  # Firefox偏好OGG
        elif 'safari' in user_agent:
            return 'mp3'  # Safari偏好MP3
        else:
            return 'wav'  # 默认最兼容的格式

# 全局实例
audio_processor = AudioProcessor() 