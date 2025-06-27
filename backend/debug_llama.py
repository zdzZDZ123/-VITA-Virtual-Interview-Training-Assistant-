#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import asyncio
import logging
sys.path.append('.')

# 设置详细日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from core.config import VITAConfig
from core.qwen_llama_client import get_client_manager, initialize_clients, create_openai_client

async def debug_llama_setup():
    """调试 Llama 设置"""
    print("=== Llama 调试信息 ===")
    
    config = VITAConfig()
    
    # 检查配置
    print(f"Llama API Key: {config.get_llama_key()[:20]}..." if config.get_llama_key() else "未设置")
    print(f"Llama Base URL: {config.get_llama_base_url()}")
    print(f"Llama Chat Model: {config.get_llama_chat_model()}")
    
    # 尝试直接创建客户端
    try:
        print("\n=== 直接创建 Llama 客户端 ===")
        llama_key = config.get_llama_key()
        llama_base_url = config.get_llama_base_url()
        
        if not llama_key:
            print("✗ Llama API Key 未设置")
            return
            
        client = create_openai_client(llama_key, llama_base_url)
        print(f"✓ 客户端创建成功: {type(client)}")
        print(f"✓ 客户端类型: {client._client_type}")
        
        # 尝试健康检查
        print("\n=== 健康检查 ===")
        health_ok = await client._health_check()
        print(f"健康检查结果: {health_ok}")
        
        if not health_ok:
            print(f"健康检查失败原因: {client._last_error}")
        
    except Exception as e:
        print(f"✗ 直接创建客户端失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 检查全局客户端管理器
    print("\n=== 全局客户端管理器 ===")
    try:
        initialize_clients()
        manager = get_client_manager()
        
        print(f"注册的客户端: {list(manager._clients.keys())}")
        print(f"当前客户端: {manager._current_client}")
        print(f"优先 Llama: {manager._prefer_llama}")
        print(f"启用备用: {manager._fallback_enabled}")
        
        # 获取客户端状态
        status = manager.get_client_status()
        print(f"\n客户端状态: {status}")
        
        # 尝试获取健康的 Llama 客户端
        llama_client = await manager.get_healthy_client(provider_type='llama')
        if llama_client:
            print("✓ 成功获取健康的 Llama 客户端")
        else:
            print("✗ 无法获取健康的 Llama 客户端")
            
    except Exception as e:
        print(f"✗ 客户端管理器错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_llama_setup())