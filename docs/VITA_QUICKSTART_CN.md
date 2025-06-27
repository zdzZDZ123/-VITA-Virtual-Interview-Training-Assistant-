# VITA 快速开始指南

## 🚀 快速开始（5分钟）

### 前置要求
- Windows 10/11
- Python 3.11+（[下载地址](https://www.python.org/downloads/)）
- Node.js 18+（[下载地址](https://nodejs.org/)）
- Git（[下载地址](https://git-scm.com/)）

### 步骤1：克隆项目
```bash
git clone https://github.com/your-repo/vita.git
cd vita
```

### 步骤2：运行快速修复脚本
```bash
quick_fix_vita.bat
```
这个脚本会自动：
- ✅ 检查环境
- ✅ 创建虚拟环境
- ✅ 使用国内镜像安装依赖
- ✅ 创建必要的目录
- ✅ 生成配置文件

### 步骤3：配置API密钥
编辑 `.env` 文件，配置您的API密钥：
```env
# Llama API配置（第三方Llama API服务）
LLAMA_API_KEY=LLM|your-llama-api-key-here
LLAMA_API_BASE_URL=https://api.llama-api.com/v1

# Qwen API配置（阿里云通义千问）
QWEN_API_KEY=__REMOVED_API_KEY__

# 双API切换配置
USE_QWEN_FALLBACK=true
PREFER_LLAMA=true
ENABLE_AUTO_SWITCH=true
```

### 步骤4：启动服务
```bash
start_vita_all.bat
```

### 步骤5：访问应用
打开浏览器访问：http://localhost:3000

## 🔧 常见问题解决

### 1. 网络代理问题
如果您在公司网络或需要代理：
```bash
configure_proxy.bat
```

### 2. 无法访问外网
准备离线安装包：
```bash
# 在有网络的机器上
offline_install_helper.bat

# 将 offline_packages 文件夹复制到目标机器
# 运行离线安装脚本
offline_install_python.bat
offline_install_node.bat
```

### 3. 端口被占用
修改 `.env` 文件中的端口配置：
```env
BACKEND_PORT=8001  # 默认8000
FRONTEND_PORT=3001  # 默认3000
```

### 4. API连接问题
如果API调用失败，请检查：
- 网络连接是否正常
- API密钥是否正确
- API服务是否可用
- 代理设置是否正确

## 📱 功能测试

### 1. 文字面试
- 访问 http://localhost:3000
- 输入职位描述
- 选择面试类型
- 开始对话

### 2. 语音面试
- 点击"语音面试"按钮
- 允许麦克风权限
- 按住说话按钮录音

### 3. 数字人面试
- 选择"数字人模式"
- 等待3D模型加载
- 开始互动

## 🛠️ 开发模式

### 后端开发
```bash
cd backend
venv\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 前端开发
```bash
cd frontend
npm run dev
```

### 运行测试
```bash
# 后端测试
cd backend
pytest

# 前端测试
cd frontend
npm test
```

## 📊 项目结构

```
vita/
├── backend/          # FastAPI后端
├── frontend/         # React前端
├── vision_service/   # 视觉分析服务
├── .env             # 环境配置
├── quick_fix_vita.bat    # 快速修复脚本
├── start_vita_all.bat    # 启动所有服务
└── configure_proxy.bat   # 代理配置工具
```

## 🆘 获取帮助

### 查看日志
- 后端日志：`backend/logs/`
- 前端控制台：F12 打开浏览器开发者工具

### 社区支持
- GitHub Issues：[提交问题](https://github.com/your-repo/vita/issues)
- 技术文档：查看 `VITA_PROJECT_ANALYSIS.md`

### 联系方式
- 邮箱：support@vita-ai.com
- 微信群：扫码加入技术交流群

## ⚡ 性能优化建议

1. **API响应优化**
   - 选择合适的模型规格
   - 使用缓存减少重复请求
   - 启用并发请求处理

2. **启用Redis缓存**
   - 安装Redis：https://github.com/tporadowski/redis/releases
   - 配置`.env`：`REDIS_URL=redis://localhost:6379`

3. **网络优化**
   - 使用CDN加速
   - 配置合适的超时时间
   - 启用请求重试机制

---

祝您使用愉快！如有问题，请随时反馈。 🎉 