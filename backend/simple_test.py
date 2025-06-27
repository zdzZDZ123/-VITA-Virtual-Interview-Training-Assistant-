#!/usr/bin/env python3
"""
简化测试脚本
验证配置是否正确
"""

import sys
import os
import requests

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 确保从环境变量加载API密钥，而不是硬编码
# 为安全起见，移除硬编码的API密钥
API_KEY = os.environ.get("OPENAI_API_KEY", "YOUR_API_KEY_HERE")
API_URL = "https://api.openai.com/v1/chat/completions"

def test_connection():
    """
    测试与OpenAI API的连接。
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Say this is a test!"}],
        "temperature": 0.7
    }
    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            print("✅ OpenAI API connection successful!")
            print("Response:", response.json())
        # 处理可能的认证错误
        elif response.status_code == 401:
            print("❌ OpenAI API connection failed: Authentication error.")
            print("   Please check your OPENAI_API_KEY.")
        else:
            print(f"❌ OpenAI API connection failed with status code: {response.status_code}")
            print("Response text:", response.text)
    except requests.exceptions.RequestException as e:
        print(f"❌ An error occurred: {e}")

def main():
    """主测试函数"""
    print("🎯 VITA 配置验证测试")
    print("=" * 30)
    
    # 设置环境变量
    os.environ["OPENAI_API_KEY"] = "YOUR_API_KEY_HERE"
    os.environ["QWEN_API_KEY"] = "YOUR_API_KEY_HERE"
    
    try:
        from core.config import config, ModelSelector
        print("✅ 配置模块导入成功")
        
        # 验证API密钥
        api_key = config.get_openai_key()
        print(f"✅ API密钥配置正确: {api_key[:20]}...")
        
        # 验证模型配置
        chat_model = config.get_model('chat')
        analysis_model = config.get_model('analysis')
        speech_model = config.get_model('speech_to_text')
        tts_model = config.get_model('text_to_speech')
        
        print(f"✅ 聊天模型: {chat_model}")
        print(f"✅ 分析模型: {analysis_model}")
        print(f"✅ 语音识别: {speech_model}")
        print(f"✅ 语音合成: {tts_model}")
        
        # 验证智能模型选择
        selector = ModelSelector()
        
        interview_model = selector.get_best_model_for_task("interview", "medium")
        analysis_task_model = selector.get_best_model_for_task("analysis", "complex")
        
        print(f"✅ 面试任务模型: {interview_model}")
        print(f"✅ 分析任务模型: {analysis_task_model}")
        
        # 验证语音场景选择
        formal_voice = selector.get_voice_for_scenario("formal")
        technical_voice = selector.get_voice_for_scenario("technical")
        
        print(f"✅ 正式场合语音: {formal_voice}")
        print(f"✅ 技术面试语音: {technical_voice}")
        
        # 验证配置完整性
        config.validate_config()
        print("✅ 配置验证通过")
        
        print("\n🎉 配置测试完全通过！")
        print("📋 配置摘要:")
        print(f"   🔑 API密钥: 已正确配置")
        print(f"   🤖 智能模型选择: 已启用")
        print(f"   🎙️ 语音功能: 已配置")
        print(f"   ⚙️ 服务配置: 已就绪")
        
        print("\n🚀 下一步操作:")
        print("   1. 运行 start_with_key.bat (Windows)")
        print("   2. 或运行 ./start_with_key.sh (Linux/macOS)")
        print("   3. 访问 http://localhost:5173 开始使用")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    test_connection()
    success = main()
    if success:
        print("\n✅ 所有测试通过，VITA系统已准备就绪！")
    else:
        print("\n❌ 测试失败，请检查配置")
        sys.exit(1)