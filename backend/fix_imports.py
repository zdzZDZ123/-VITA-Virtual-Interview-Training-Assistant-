#!/usr/bin/env python3
"""
批量修复backend目录中的导入路径
将 'from backend.xxx' 改为 'from xxx'
"""

import os
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    """修复单个文件中的导入"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 修复各种backend导入模式
        patterns = [
            (r'from backend\.core\.', 'from core.'),
            (r'from backend\.api\.', 'from api.'),
            (r'from backend\.models\.', 'from models.'),
            (r'from backend\.tests\.', 'from tests.'),
            (r'import backend\.core\.', 'import core.'),
            (r'import backend\.api\.', 'import api.'),
            (r'import backend\.models\.', 'import models.'),
            (r'import backend\.tests\.', 'import tests.'),
        ]
        
        changes_made = False
        for pattern, replacement in patterns:
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                changes_made = True
                content = new_content
        
        if changes_made:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 修复: {file_path}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ 错误处理 {file_path}: {e}")
        return False

def main():
    """主函数"""
    backend_dir = Path('.')
    python_files = list(backend_dir.rglob('*.py'))
    
    print(f"🔍 找到 {len(python_files)} 个Python文件")
    
    fixed_count = 0
    for py_file in python_files:
        if fix_imports_in_file(py_file):
            fixed_count += 1
    
    print(f"🎉 完成！修复了 {fixed_count} 个文件的导入路径")

if __name__ == "__main__":
    main() 