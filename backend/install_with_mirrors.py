#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VITA项目依赖安装脚本 - 使用国内镜像源
支持自动检测最快镜像源并安装所有依赖
"""

import subprocess
import sys
import time
import urllib.request
import os
from pathlib import Path

# 国内主要镜像源配置
MIRRORS = {
    "清华大学": "https://pypi.tuna.tsinghua.edu.cn/simple",
    "阿里云": "https://mirrors.aliyun.com/pypi/simple",
    "豆瓣": "https://pypi.douban.com/simple",
    "中科大": "https://pypi.mirrors.ustc.edu.cn/simple",
    "华为云": "https://mirrors.huaweicloud.com/repository/pypi/simple",
    "腾讯云": "https://mirrors.cloud.tencent.com/pypi/simple"
}

def test_mirror_speed(mirror_url, timeout=5):
    """测试镜像源速度"""
    try:
        start_time = time.time()
        response = urllib.request.urlopen(mirror_url, timeout=timeout)
        end_time = time.time()
        if response.status == 200:
            return end_time - start_time
    except Exception:
        pass
    return float('inf')

def find_fastest_mirror():
    """找到最快的镜像源"""
    print("🔍 正在测试镜像源速度...")
    fastest_mirror = None
    fastest_time = float('inf')
    fastest_name = None
    
    for name, url in MIRRORS.items():
        print(f"   测试 {name}: {url}")
        speed = test_mirror_speed(url)
        if speed < fastest_time:
            fastest_time = speed
            fastest_mirror = url
            fastest_name = name
        print(f"   响应时间: {speed:.2f}s" if speed != float('inf') else "   连接失败")
    
    if fastest_mirror:
        print(f"\n✅ 最快镜像源: {fastest_name} ({fastest_time:.2f}s)")
        return fastest_mirror, fastest_name
    else:
        print("\n⚠️ 所有镜像源都无法连接，将使用默认源")
        return None, None

def run_command(cmd, description):
    """执行命令并显示进度"""
    print(f"\n🔧 {description}")
    print(f"执行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ 成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 失败: {e}")
        if e.stdout:
            print(f"输出: {e.stdout}")
        if e.stderr:
            print(f"错误: {e.stderr}")
        return False

def install_dependencies(mirror_url=None, mirror_name=None):
    """安装项目依赖"""
    base_cmd = [sys.executable, "-m", "pip", "install"]
    
    if mirror_url:
        base_cmd.extend(["-i", mirror_url])
        print(f"\n📦 使用镜像源安装依赖: {mirror_name}")
    else:
        print("\n📦 使用默认源安装依赖")
    
    # 升级pip
    pip_cmd = base_cmd + ["--upgrade", "pip"]
    if not run_command(pip_cmd, "升级pip"):
        print("⚠️ pip升级失败，继续安装依赖")
    
    # 安装基础依赖
    requirements_file = Path("requirements.txt")
    if requirements_file.exists():
        req_cmd = base_cmd + ["-r", "requirements.txt"]
        if not run_command(req_cmd, "安装requirements.txt中的依赖"):
            return False
    
    # 安装特殊依赖
    special_packages = [
        ("openai>=1.35.0", "安装OpenAI客户端"),
        ("faster-whisper>=1.0.0", "安装Faster Whisper"),
        ("torch>=2.2.0,<2.3.0", "安装PyTorch"),
        ("torchaudio>=2.2.0", "安装TorchAudio")
    ]
    
    for package, description in special_packages:
        pkg_cmd = base_cmd + [package]
        if not run_command(pkg_cmd, description):
            print(f"⚠️ {description}失败，可能需要手动安装")
    
    return True

def setup_pip_config(mirror_url, mirror_name):
    """设置pip配置文件"""
    pip_config = f"""[global]
index-url = {mirror_url}
trusted-host = {mirror_url.split('//')[1].split('/')[0]}
timeout = 120

[install]
trusted-host = 
    pypi.tuna.tsinghua.edu.cn
    mirrors.aliyun.com
    pypi.douban.com
    pypi.mirrors.ustc.edu.cn
    mirrors.huaweicloud.com
    mirrors.cloud.tencent.com
"""
    
    try:
        with open("pip.ini", "w", encoding="utf-8") as f:
            f.write(pip_config)
        print(f"✅ 已更新pip配置文件，使用{mirror_name}镜像源")
        return True
    except Exception as e:
        print(f"❌ 更新pip配置失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 VITA项目依赖安装脚本")
    print("=" * 50)
    
    # 检查当前目录
    if not Path("requirements.txt").exists():
        print("❌ 未找到requirements.txt文件，请在backend目录下运行此脚本")
        return 1
    
    # 选择安装方式
    print("\n请选择安装方式:")
    print("1. 自动检测最快镜像源")
    print("2. 手动选择镜像源")
    print("3. 使用默认源")
    
    try:
        choice = input("\n请输入选择 (1-3): ").strip()
    except KeyboardInterrupt:
        print("\n\n👋 安装已取消")
        return 0
    
    mirror_url = None
    mirror_name = None
    
    if choice == "1":
        mirror_url, mirror_name = find_fastest_mirror()
    elif choice == "2":
        print("\n可用镜像源:")
        for i, (name, url) in enumerate(MIRRORS.items(), 1):
            print(f"{i}. {name}: {url}")
        
        try:
            mirror_choice = int(input("\n请选择镜像源 (1-6): ")) - 1
            if 0 <= mirror_choice < len(MIRRORS):
                mirror_name, mirror_url = list(MIRRORS.items())[mirror_choice]
            else:
                print("❌ 无效选择，使用默认源")
        except (ValueError, KeyboardInterrupt):
            print("❌ 无效输入，使用默认源")
    
    # 更新pip配置
    if mirror_url:
        setup_pip_config(mirror_url, mirror_name)
    
    # 安装依赖
    success = install_dependencies(mirror_url, mirror_name)
    
    if success:
        print("\n🎉 依赖安装完成!")
        print("\n📋 安装后检查:")
        print("   - 运行 'python -c \"import torch; print(torch.__version__)\"' 检查PyTorch")
        print("   - 运行 'python -c \"import whisper; print('Whisper OK')\"' 检查Whisper")
        print("   - 运行 'python -c \"import fastapi; print('FastAPI OK')\"' 检查FastAPI")
        return 0
    else:
        print("\n❌ 依赖安装失败，请检查错误信息")
        return 1

if __name__ == "__main__":
    sys.exit(main())