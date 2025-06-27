# Whisper 离线安装快速指南

本文档提供VITA项目中Whisper离线安装的快速指南和文件说明。

## 📁 相关文件

### 📖 文档文件
- `WHISPER_OFFLINE_INSTALLATION.md` - 详细的离线安装指南
- `backend/LOCAL_WHISPER_README.md` - 本地Whisper使用说明（已更新离线安装部分）
- `WHISPER_OFFLINE_SETUP.md` - 本文件，快速指南

### 🔧 脚本文件

#### 依赖下载脚本（在联网环境使用）
- `download_whisper_deps.bat` - Windows依赖下载脚本
- `download_whisper_deps.sh` - Linux/macOS依赖下载脚本

#### 离线安装脚本（在目标环境使用）
- `install_whisper_offline.bat` - Windows离线安装脚本
- `install_whisper_offline.sh` - Linux/macOS离线安装脚本

#### 验证脚本
- `verify_whisper_installation.py` - 安装验证脚本

## 🚀 快速开始

### 步骤1: 下载依赖（联网环境）

在有网络连接的机器上运行：

**Windows:**
```cmd
download_whisper_deps.bat
```

**Linux/macOS:**
```bash
bash download_whisper_deps.sh
```

这会创建 `whisper_pkgs` 目录并下载所有必要的依赖包。

### 步骤2: 传输文件

将以下内容拷贝到目标机器：
- 整个 `whisper_pkgs` 目录
- VITA项目代码
- 安装脚本

### 步骤3: 离线安装（目标环境）

在目标机器上运行：

**Windows:**
```cmd
install_whisper_offline.bat
```

**Linux/macOS:**
```bash
bash install_whisper_offline.sh
```

### 步骤4: 验证安装

```bash
python verify_whisper_installation.py
```

## 📋 依赖包列表

根据用户提供的信息，Whisper需要以下依赖：

### 核心依赖
- `torch` - PyTorch深度学习框架
- `numpy` - 数值计算库
- `tqdm` - 进度条库
- `more-itertools` - 迭代器工具
- `tiktoken` - 文本编码库

### 构建依赖
- `setuptools` (>=61.2) - Python包构建工具
- `wheel` - Python包分发格式

## ⚠️ 重要提示

1. **PyTorch版本选择**
   - 建议手动从 https://pytorch.org/get-started/locally/ 下载匹配的PyTorch版本
   - 确保选择与你的CUDA版本和Python版本兼容的wheel文件

2. **tiktoken编译问题**
   - 如果遇到编译错误，可能需要安装Rust环境
   - 或者下载预编译的wheel文件

3. **目录结构**
   ```
   VITA项目根目录/
   ├── whisper_pkgs/          # 依赖包目录
   ├── backend/
   │   └── whisper-main/      # Whisper源码（可选）
   ├── install_whisper_offline.bat
   ├── install_whisper_offline.sh
   └── verify_whisper_installation.py
   ```

## 🔧 配置使用

安装完成后，在 `.env` 文件中启用本地Whisper：

```env
USE_LOCAL_WHISPER=true
LOCAL_WHISPER_MODEL=medium
LOCAL_WHISPER_DEVICE=auto
LOCAL_WHISPER_COMPUTE_TYPE=float16
```

## 🐛 故障排除

如果遇到问题，请：

1. 运行验证脚本检查安装状态
2. 查看详细安装指南 `WHISPER_OFFLINE_INSTALLATION.md`
3. 检查Python版本兼容性（建议3.8+）
4. 确认所有依赖包都在 `whisper_pkgs` 目录中

## 📞 支持

如需更多帮助，请参考：
- `WHISPER_OFFLINE_INSTALLATION.md` - 详细安装指南
- `backend/LOCAL_WHISPER_README.md` - 本地Whisper使用说明
- 运行 `python verify_whisper_installation.py` 获取详细诊断信息