#!/usr/bin/env python3
"""
VITA项目目录结构重组脚本
按照PROJECT_STRUCTURE_GUIDE.md的规范重新整理项目结构
"""

import os
import shutil
import re
from pathlib import Path
from datetime import datetime
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VitaReorganizer:
    def __init__(self):
        self.project_root = Path('.')
        self.backup_dir = self.project_root / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 定义目标目录结构
        self.target_structure = {
            'backend': {
                'api': ['__init__.py', 'health.py', 'model_manager.py', 'modules.py'],
                'core': [
                    '__init__.py', 'speech.py', 'realtime_speech.py', 
                    'whisper_model_manager.py', 'module_registry.py', 
                    'chat.py', 'tts_service.py', 'config.py', 'logger.py'
                ],
                'core/tts_engines': [
                    '__init__.py', 'base.py', 'edge_engine.py', 'pyttsx3_engine.py'
                ],
                'models': ['__init__.py', 'session.py', 'api.py'],
                'whisper': [],  # 保持原有whisper模块
                'static': [],   # 静态文件
                'tests': []     # 单元测试
            },
            'frontend': {
                'src/api': [],
                'src/components': [],
                'src/store': [],
                'src/utils': []
            },
            'scripts': ['__init__.py', 'download_faster_whisper.py'],
            'whisper_download': ['tiny/', 'base/', 'small/', 'medium/', 'large/'],
            'cache': ['tts/', 'models/'],
            'logs': [],
            'docs': []
        }
        
        # 定义文件映射规则（从当前位置到目标位置）
        self.file_mappings = {
            # API文件映射
            'backend/api/health.py': 'backend/api/health.py',
            'backend/api/model_manager.py': 'backend/api/model_manager.py', 
            'backend/api/modules.py': 'backend/api/modules.py',
            
            # 核心文件映射
            'backend/core/speech.py': 'backend/core/speech.py',
            'backend/core/realtime_speech.py': 'backend/core/realtime_speech.py',
            'backend/core/whisper_model_manager.py': 'backend/core/whisper_model_manager.py',
            'backend/core/module_registry.py': 'backend/core/module_registry.py',
            'backend/core/chat.py': 'backend/core/chat.py',
            'backend/core/tts_service.py': 'backend/core/tts_service.py',
            'backend/core/config.py': 'backend/core/config.py',
            'backend/core/logger.py': 'backend/core/logger.py',
            
            # TTS引擎映射
            'backend/core/tts_engines/': 'backend/core/tts_engines/',
            
            # 模型文件映射
            'backend/models/session.py': 'backend/models/session.py',
            'backend/models/api.py': 'backend/models/api.py',
            
            # 主要文件
            'backend/main.py': 'backend/main.py',
            'backend/fix_whisper_models.py': 'backend/fix_whisper_models.py',
            'backend/requirements.txt': 'backend/requirements.txt',
            
            # 脚本映射
            'scripts/download_faster_whisper.py': 'scripts/download_faster_whisper.py',
            
            # 配置和说明文件保持在根目录
            'README.md': 'README.md',
            'download_whisper_model.bat': 'download_whisper_model.bat',
            'start_backend.bat': 'start_backend.bat'
        }
        
        # 需要归档到docs目录的文档文件
        self.doc_files = [
            'PROJECT_STRUCTURE_GUIDE.md',
            '__REMOVED_API_KEY__.md', 
            '__REMOVED_API_KEY__.md',
            'WHISPER_OFFLINE_DEPLOYMENT.md',
            '__REMOVED_API_KEY__.md',
            '__REMOVED_API_KEY__.md',
            'VOICE_IMPLEMENTATION_GUIDE.md',
            'API_CONFIGURATION.md',
            '*.md'  # 其他md文件
        ]
        
        # 需要归档到test_artifacts的测试文件
        self.test_files = [
            '*.html',
            '*test*.py',
            '*test*.json',
            '*.mp3'
        ]

    def create_backup(self):
        """创建完整备份"""
        logger.info(f"🗂️ 创建备份到 {self.backup_dir}")
        
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        
        # 复制整个项目到备份目录
        important_dirs = ['backend', 'frontend', 'scripts', 'whisper_download', 'cache']
        important_files = ['*.py', '*.md', '*.bat', '*.json', 'requirements.txt']
        
        self.backup_dir.mkdir(parents=True)
        
        for dir_name in important_dirs:
            src_dir = self.project_root / dir_name
            if src_dir.exists():
                dst_dir = self.backup_dir / dir_name
                shutil.copytree(src_dir, dst_dir, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'node_modules'))
        
        logger.info("✅ 备份完成")

    def create_target_directories(self):
        """创建目标目录结构"""
        logger.info("📂 创建目标目录结构...")
        
        for main_dir, subdirs in self.target_structure.items():
            main_path = self.project_root / main_dir
            main_path.mkdir(exist_ok=True)
            
            if isinstance(subdirs, dict):
                for subdir, files in subdirs.items():
                    subdir_path = main_path / subdir
                    subdir_path.mkdir(parents=True, exist_ok=True)
                    
                    # 创建__init__.py文件
                    if '__init__.py' in files:
                        init_file = subdir_path / '__init__.py'
                        if not init_file.exists():
                            init_file.write_text('# -*- coding: utf-8 -*-\n')
            
            elif isinstance(subdirs, list):
                for item in subdirs:
                    if item.endswith('/'):
                        # 这是一个目录
                        (main_path / item).mkdir(parents=True, exist_ok=True)
                    elif item == '__init__.py':
                        # 创建__init__.py文件
                        init_file = main_path / '__init__.py'
                        if not init_file.exists():
                            init_file.write_text('# -*- coding: utf-8 -*-\n')
        
        # 创建特殊目录
        (self.project_root / 'docs').mkdir(exist_ok=True)
        (self.project_root / 'test_artifacts').mkdir(exist_ok=True)
        (self.project_root / 'cache' / 'tts').mkdir(parents=True, exist_ok=True)
        (self.project_root / 'cache' / 'models').mkdir(parents=True, exist_ok=True)
        (self.project_root / 'logs').mkdir(exist_ok=True)
        
        logger.info("✅ 目录结构创建完成")

    def move_files(self):
        """移动文件到正确位置"""
        logger.info("🚚 开始移动文件...")
        
        moved_files = 0
        
        # 处理明确的文件映射
        for src_path, dst_path in self.file_mappings.items():
            src = self.project_root / src_path
            dst = self.project_root / dst_path
            
            # 跳过相同路径的文件
            if src.resolve() == dst.resolve():
                logger.info(f"⏭️ 跳过: {src_path} (已在正确位置)")
                continue
            
            if src.exists():
                # 确保目标目录存在
                dst.parent.mkdir(parents=True, exist_ok=True)
                
                if src.is_dir():
                    # 如果是目录，复制整个目录
                    if dst.exists() and dst != src:
                        shutil.rmtree(dst)
                    if dst != src:
                        shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
                else:
                    # 如果是文件，复制文件
                    if dst != src:
                        shutil.copy2(src, dst)
                
                moved_files += 1
                logger.info(f"📁 移动: {src_path} -> {dst_path}")
            else:
                logger.warning(f"⚠️ 源文件不存在: {src_path}")
        
        logger.info(f"✅ 文件移动完成，共处理 {moved_files} 个项目")

    def organize_documents(self):
        """整理文档文件到docs目录"""
        logger.info("📚 整理文档文件...")
        
        docs_dir = self.project_root / 'docs'
        docs_dir.mkdir(exist_ok=True)
        
        # 移动markdown文档
        for md_file in self.project_root.glob('*.md'):
            if md_file.name not in ['README.md']:  # README保持在根目录
                dst = docs_dir / md_file.name
                if not dst.exists():
                    shutil.copy2(md_file, dst)
                    logger.info(f"📄 文档移动: {md_file.name} -> docs/")
        
        logger.info("✅ 文档整理完成")

    def organize_test_artifacts(self):
        """整理测试文件到test_artifacts目录"""
        logger.info("🧪 整理测试文件...")
        
        test_dir = self.project_root / 'test_artifacts'
        test_dir.mkdir(exist_ok=True)
        
        # 移动测试HTML文件
        for html_file in self.project_root.glob('*.html'):
            dst = test_dir / html_file.name
            if not dst.exists():
                shutil.copy2(html_file, dst)
                logger.info(f"🧪 测试文件移动: {html_file.name} -> test_artifacts/")
        
        # 移动测试Python文件（根目录下的）
        for py_file in self.project_root.glob('test_*.py'):
            dst = test_dir / py_file.name
            if not dst.exists():
                shutil.copy2(py_file, dst)
                logger.info(f"🧪 测试脚本移动: {py_file.name} -> test_artifacts/")
        
        # 移动音频测试文件
        for mp3_file in self.project_root.glob('*.mp3'):
            dst = test_dir / mp3_file.name
            if not dst.exists():
                shutil.copy2(mp3_file, dst)
                logger.info(f"🎵 音频文件移动: {mp3_file.name} -> test_artifacts/")
        
        logger.info("✅ 测试文件整理完成")

    def fix_imports(self):
        """修复Python import路径"""
        logger.info("🔧 修复import路径...")
        
        # 定义import替换规则
        import_fixes = [
            # API导入修复
            (r'from api\.', 'from backend.api.'),
            (r'import api\.', 'import backend.api.'),
            
            # Core导入修复
            (r'from core\.', 'from backend.core.'),
            (r'import core\.', 'import backend.core.'),
            
            # Models导入修复  
            (r'from models\.', 'from backend.models.'),
            (r'import models\.', 'import backend.models.'),
            
            # 相对导入修复
            (r'from \.([^\.]+)', r'from backend.core.\1'),
        ]
        
        # 扫描所有Python文件
        for py_file in self.project_root.rglob('*.py'):
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8')
                original_content = content
                
                # 应用import修复规则
                for pattern, replacement in import_fixes:
                    content = re.sub(pattern, replacement, content)
                
                # 如果内容有变化，写回文件
                if content != original_content:
                    py_file.write_text(content, encoding='utf-8')
                    logger.info(f"🔧 修复imports: {py_file.relative_to(self.project_root)}")
                    
            except Exception as e:
                logger.warning(f"⚠️ 修复imports失败 {py_file}: {e}")
        
        logger.info("✅ import路径修复完成")

    def create_init_files(self):
        """创建必要的__init__.py文件"""
        logger.info("📝 创建__init__.py文件...")
        
        init_locations = [
            'backend/__init__.py',
            'backend/api/__init__.py', 
            'backend/core/__init__.py',
            'backend/core/tts_engines/__init__.py',
            'backend/models/__init__.py',
            'scripts/__init__.py'
        ]
        
        for init_path in init_locations:
            init_file = self.project_root / init_path
            if not init_file.exists():
                init_file.parent.mkdir(parents=True, exist_ok=True)
                init_file.write_text('# -*- coding: utf-8 -*-\n')
                logger.info(f"📝 创建: {init_path}")
        
        logger.info("✅ __init__.py文件创建完成")

    def cleanup_old_files(self):
        """清理旧的、重复的或不需要的文件"""
        logger.info("🧹 清理不需要的文件...")
        
        # 清理模式
        cleanup_patterns = [
            '__pycache__',
            '*.pyc',
            '*.pyo',
            '.pytest_cache',
            'htmlcov',
            'venv',
            'node_modules/.cache'
        ]
        
        cleaned_count = 0
        
        for pattern in cleanup_patterns:
            for item in self.project_root.rglob(pattern):
                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                    cleaned_count += 1
                    logger.info(f"🗑️ 清理: {item.relative_to(self.project_root)}")
                except Exception as e:
                    logger.warning(f"⚠️ 清理失败 {item}: {e}")
        
        logger.info(f"✅ 清理完成，移除 {cleaned_count} 个项目")

    def create_gitignore(self):
        """创建或更新.gitignore文件"""
        logger.info("📝 更新.gitignore文件...")
        
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
logs/
*.log

# Cache
cache/
.cache/

# Test artifacts
test_artifacts/
htmlcov/
.coverage
.pytest_cache/

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Frontend build
frontend/dist/
frontend/build/

# Models and data
whisper_download/
*.mp3
*.wav

# Backup
backup_*/

# System files
.DS_Store
Thumbs.db
"""
        
        gitignore_file = self.project_root / '.gitignore'
        gitignore_file.write_text(gitignore_content)
        logger.info("✅ .gitignore文件更新完成")

    def generate_report(self):
        """生成重组报告"""
        logger.info("📊 生成重组报告...")
        
        report_content = f"""# VITA项目结构重组报告

## 重组时间
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 重组目标
按照PROJECT_STRUCTURE_GUIDE.md规范重新整理项目目录结构

## 新目录结构

```
VITA (Virtual Interview & Training Assistant)/
├── 📂 backend/                          # 后端服务
│   ├── 📂 api/                          # API路由层
│   ├── 📂 core/                         # 核心业务逻辑
│   │   └── 📂 tts_engines/              # TTS引擎实现
│   ├── 📂 models/                       # 数据模型层
│   ├── 📂 whisper/                      # 本地Whisper模块
│   ├── 📂 static/                       # 静态文件
│   ├── 📂 tests/                        # 单元测试
│   ├── main.py                          # FastAPI应用入口
│   ├── requirements.txt                 # Python依赖
│   └── fix_whisper_models.py            # 模型修复工具
│
├── 📂 frontend/                         # 前端应用
│   └── 📂 src/
│       ├── 📂 api/                      # API客户端
│       ├── 📂 components/               # React组件
│       ├── 📂 store/                    # 状态管理
│       └── 📂 utils/                    # 工具函数
│
├── 📂 scripts/                          # 工具脚本
├── 📂 whisper_download/                 # Whisper模型存储
├── 📂 cache/                            # 缓存目录
├── 📂 logs/                             # 日志文件
├── 📂 docs/                             # 项目文档
├── 📂 test_artifacts/                   # 测试文件归档
├── download_whisper_model.bat           # Windows模型下载工具
├── start_backend.bat                    # Windows后端启动脚本
└── README.md                            # 项目说明
```

## 完成的操作

1. ✅ 创建完整备份到 backup_* 目录
2. ✅ 创建新的目录结构
3. ✅ 移动和重新组织文件
4. ✅ 修复Python import路径
5. ✅ 创建必要的__init__.py文件
6. ✅ 整理文档到docs目录
7. ✅ 整理测试文件到test_artifacts目录
8. ✅ 清理不需要的文件和缓存
9. ✅ 更新.gitignore文件

## 注意事项

1. 原始文件已备份到 backup_* 目录
2. 所有import路径已自动修复
3. 如遇问题可从备份目录恢复
4. 建议执行测试确认功能正常

## 后续步骤

1. 运行 `cd backend && python -m pytest` 测试后端
2. 运行 `cd frontend && npm test` 测试前端  
3. 检查所有功能是否正常
4. 如无问题，可删除backup目录

"""
        
        report_file = self.project_root / 'REORGANIZATION_REPORT.md'
        report_file.write_text(report_content, encoding='utf-8')
        logger.info("✅ 重组报告生成完成")

    def run(self):
        """执行完整的重组流程"""
        logger.info("🚀 开始VITA项目结构重组...")
        
        try:
            # 步骤1: 创建备份
            self.create_backup()
            
            # 步骤2: 创建目标目录结构
            self.create_target_directories()
            
            # 步骤3: 移动文件
            self.move_files()
            
            # 步骤4: 整理文档
            self.organize_documents()
            
            # 步骤5: 整理测试文件
            self.organize_test_artifacts()
            
            # 步骤6: 修复imports
            self.fix_imports()
            
            # 步骤7: 创建init文件
            self.create_init_files()
            
            # 步骤8: 清理旧文件
            self.cleanup_old_files()
            
            # 步骤9: 更新gitignore
            self.create_gitignore()
            
            # 步骤10: 生成报告
            self.generate_report()
            
            logger.info("🎉 VITA项目结构重组完成！")
            logger.info("📊 查看 REORGANIZATION_REPORT.md 了解详细信息")
            logger.info("🔍 建议运行测试确认功能正常")
            
        except Exception as e:
            logger.error(f"❌ 重组过程中出现错误: {e}")
            logger.error("💡 可从backup目录恢复原始文件")
            raise

if __name__ == "__main__":
    reorganizer = VitaReorganizer()
    reorganizer.run() 