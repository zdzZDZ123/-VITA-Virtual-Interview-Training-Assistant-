#!/usr/bin/env python3
"""
最终文件清理脚本 - 完成VITA项目目录整理
"""

import shutil
from pathlib import Path
import os

def final_cleanup():
    print("🧹 开始最终文件清理...")
    
    # 确保目标目录存在
    docs_dir = Path('docs')
    test_artifacts_dir = Path('test_artifacts')
    docs_dir.mkdir(exist_ok=True)
    test_artifacts_dir.mkdir(exist_ok=True)
    
    moved_count = 0
    
    # 1. 移动所有.md文档文件到docs目录
    keep_in_root = ['README.md', 'REORGANIZATION_REPORT.md']
    for md_file in Path('.').glob('*.md'):
        if md_file.name not in keep_in_root:
            dst = docs_dir / md_file.name
            if not dst.exists():
                shutil.move(str(md_file), str(dst))
                print(f"📄 移动文档: {md_file.name} -> docs/")
                moved_count += 1
    
    # 2. 移动所有.html文件到test_artifacts
    for html_file in Path('.').glob('*.html'):
        dst = test_artifacts_dir / html_file.name
        if not dst.exists():
            shutil.move(str(html_file), str(dst))
            print(f"🌐 移动HTML: {html_file.name} -> test_artifacts/")
            moved_count += 1
    
    # 3. 移动所有.mp3音频文件到test_artifacts
    for mp3_file in Path('.').glob('*.mp3'):
        dst = test_artifacts_dir / mp3_file.name
        if not dst.exists():
            shutil.move(str(mp3_file), str(dst))
            print(f"🎵 移动音频: {mp3_file.name} -> test_artifacts/")
            moved_count += 1
    
    # 4. 移动测试相关的Python文件到test_artifacts
    test_files = [
        'test_*.py', '*test*.py', '*_test.py', 'vita_*.py',
        'voice_interview_*.py', 'simple_backend*.py', 
        'optimize*.py', '*verification*.py', 'bug_fix*.py',
        'quick_start_test.py', 'local_voice_interview_test.py'
    ]
    
    keep_scripts = ['reorganize_vita_structure.py', 'final_cleanup.py']
    
    for pattern in test_files:
        for py_file in Path('.').glob(pattern):
            if py_file.name not in keep_scripts:
                dst = test_artifacts_dir / py_file.name
                if not dst.exists():
                    shutil.move(str(py_file), str(dst))
                    print(f"🐍 移动测试脚本: {py_file.name} -> test_artifacts/")
                    moved_count += 1
    
    # 5. 移动.json文件到test_artifacts
    for json_file in Path('.').glob('*.json'):
        dst = test_artifacts_dir / json_file.name
        if not dst.exists():
            shutil.move(str(json_file), str(dst))
            print(f"📋 移动JSON: {json_file.name} -> test_artifacts/")
            moved_count += 1
    
    # 6. 移动.bat启动脚本到scripts目录
    scripts_dir = Path('scripts')
    scripts_dir.mkdir(exist_ok=True)
    
    keep_bat_in_root = ['download_whisper_model.bat']
    for bat_file in Path('.').glob('*.bat'):
        if bat_file.name not in keep_bat_in_root:
            dst = scripts_dir / bat_file.name
            if not dst.exists():
                shutil.move(str(bat_file), str(dst))
                print(f"⚙️ 移动脚本: {bat_file.name} -> scripts/")
                moved_count += 1
    
    # 7. 移动.ps1文件到scripts目录
    for ps1_file in Path('.').glob('*.ps1'):
        dst = scripts_dir / ps1_file.name
        if not dst.exists():
            shutil.move(str(ps1_file), str(dst))
            print(f"⚙️ 移动PowerShell: {ps1_file.name} -> scripts/")
            moved_count += 1
    
    # 8. 移动剩余的Python文件到适当位置
    remaining_py_files = ['main.py', 'start_vita_backend.py', 'simple_backend.py']
    for py_file in Path('.').glob('*.py'):
        if py_file.name in remaining_py_files and py_file.name not in keep_scripts:
            dst = test_artifacts_dir / py_file.name
            if not dst.exists():
                shutil.move(str(py_file), str(dst))
                print(f"🐍 移动脚本: {py_file.name} -> test_artifacts/")
                moved_count += 1
    
    print(f"✅ 最终清理完成，移动了 {moved_count} 个文件")
    
    # 9. 显示当前根目录应该保留的文件
    print("\n📂 根目录应保留的文件:")
    for item in sorted(Path('.').iterdir()):
        if item.is_file() and not item.name.startswith('.'):
            print(f"  📄 {item.name}")
        elif item.is_dir() and not item.name.startswith('.') and not item.name.startswith('backup_'):
            print(f"  📁 {item.name}/")

if __name__ == "__main__":
    final_cleanup() 