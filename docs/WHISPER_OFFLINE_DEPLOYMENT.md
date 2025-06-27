# VITA Whisper 离线部署指南

本指南介绍如何配置VITA项目使用本地Whisper模型，避免启动时的网络下载和警告信息。

## 🎯 解决的问题

- ✅ 消除启动时的 "Cannot find snapshot folder" 警告
- ✅ 支持完全离线的语音识别
- ✅ 提升模型加载速度（faster-whisper比标准whisper快2-3倍）
- ✅ 简化部署流程，无需依赖外网

## 📦 快速开始

### 1. 自动安装（推荐）

运行安装脚本，选择下载模型：

```bash
# Windows
cd backend
install_local_whisper.bat

# Linux/Mac  
cd backend
chmod +x install_local_whisper.sh
./install_local_whisper.sh
```

脚本会询问是否下载medium模型，选择 `y` 即可自动下载到本地。

### 2. 手动下载模型

```bash
# 下载推荐的medium模型
python scripts/download_faster_whisper.py medium --install-deps

# 下载其他大小的模型
python scripts/download_faster_whisper.py tiny     # 39MB，最快
python scripts/download_faster_whisper.py base     # 74MB，快速
python scripts/download_faster_whisper.py small    # 244MB，平衡
python scripts/download_faster_whisper.py large    # 1550MB，最高精度

# 强制重新下载
python scripts/download_faster_whisper.py medium --force

# 下载后验证模型
python scripts/download_faster_whisper.py medium --verify
```

## 📁 目录结构

下载后的模型文件将存储在：

```
VITA项目根目录/
├── whisper_download/
│   ├── medium/           # medium模型文件
│   │   ├── config.json
│   │   ├── model.bin
│   │   ├── tokenizer.json
│   │   └── vocabulary.txt
│   ├── large/            # large模型文件（可选）
│   └── ...
└── scripts/
    └── download_faster_whisper.py
```

## ⚙️ 配置选项

### 环境变量配置

在 `.env` 文件中添加（可选）：

```bash
# 本地模型配置
LOCAL_WHISPER_MODEL=medium                    # 模型大小
LOCAL_WHISPER_MODEL_DIR=whisper_download     # 模型目录
LOCAL_WHISPER_DEVICE=auto                    # 设备：auto/cpu/cuda
LOCAL_WHISPER_COMPUTE_TYPE=float16           # 精度：float16/int8

# 网络设置
DISABLE_WHISPER_ONLINE=true                  # 禁用在线下载
```

### 模型选择建议

| 模型 | 大小 | 速度 | 精度 | 推荐场景 |
|------|------|------|------|----------|
| tiny | 39MB | 最快 | 较低 | 快速原型 |
| base | 74MB | 快 | 一般 | 开发测试 |
| small | 244MB | 中等 | 良好 | 轻量部署 |
| **medium** | **769MB** | **平衡** | **优秀** | **生产推荐** ⭐ |
| large | 1550MB | 较慢 | 最高 | 高精度需求 |

## 🚀 离线部署

### 1. 准备离线包

在有网络的机器上：

```bash
# 下载模型
python scripts/download_faster_whisper.py medium --install-deps

# 打包整个项目
tar -czf vita-offline.tar.gz . --exclude=venv --exclude=node_modules
```

### 2. 部署到离线环境

在目标机器上：

```bash
# 解压项目
tar -xzf vita-offline.tar.gz

# 安装Python依赖（离线包）
pip install -r requirements.txt --no-index --find-links ./wheels

# 启动服务
python start_vita_backend.py
```

## 🔧 故障排除

### 常见问题

**Q: 启动时仍有警告信息**
```
WARNING:faster_whisper:An error occurred while synchronizing...
```

A: 检查模型目录是否正确：
```bash
python scripts/download_faster_whisper.py medium --verify
```

**Q: 模型加载失败**

A: 检查模型文件完整性：
```python
# 在Python中验证
from pathlib import Path
model_dir = Path("whisper_download/medium")
print(f"模型目录存在: {model_dir.exists()}")
print(f"config.json存在: {(model_dir / 'config.json').exists()}")
```

**Q: 想要切换到其他模型**

A: 修改配置或重新下载：
```bash
# 方法1：修改环境变量
export LOCAL_WHISPER_MODEL=large

# 方法2：下载新模型
python scripts/download_faster_whisper.py large
```

### 性能优化

1. **使用合适的精度**：
   - CPU: `compute_type=int8`
   - GPU: `compute_type=float16`

2. **选择合适的设备**：
   - 自动检测: `device=auto`
   - 强制CPU: `device=cpu`
   - 强制GPU: `device=cuda`

## 🎯 模型加载策略

VITA现在使用智能的多级fallback策略：

1. **本地离线模型** (`whisper_download/medium/`) - 最优选择
2. **系统缓存模型** (`~/.cache/huggingface/`) - 备用
3. **在线下载** (仅在网络可用时) - 兜底
4. **标准whisper** - 最终备用

这个策略确保在各种环境下都能正常工作，同时最大化性能和用户体验。

## 📊 性能对比

| 方案 | 启动时间 | 识别速度 | 内存占用 | 网络需求 |
|------|----------|----------|----------|----------|
| 在线下载 | 30-60s | 快 | 中等 | 需要 |
| 本地模型 | 3-5s | 最快 | 低 | 无需 |
| 标准whisper | 10-15s | 较慢 | 高 | 可选 |

使用本地模型可以显著提升启动速度和整体性能！

## 🔄 更新和维护

### 模型更新

```bash
# 更新到最新版本的模型
python scripts/download_faster_whisper.py medium --force

# 清理旧模型
rm -rf whisper_download/medium
python scripts/download_faster_whisper.py medium
```

### 清理缓存

```bash
# 清理系统缓存（释放空间）
rm -rf ~/.cache/huggingface/hub/__REMOVED_API_KEY__

# 清理本地模型
rm -rf whisper_download/
```

现在启动VITA时，将看到类似以下的友好日志输出：

```
✅ 发现本地模型: whisper_download/medium
✅ 使用本地faster-whisper模型: whisper_download/medium  
🎉 本地Whisper模型加载成功！(faster_whisper_local - medium)
```

不再有任何警告信息！🎉 