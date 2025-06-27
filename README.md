# VITA (Virtual Interview & Training Assistant)

![VITA Logo](https://via.placeholder.com/150x50/3B82F6/FFFFFF?text=VITA)

**VITA** 是一个基于AI的虚拟面试与培训助理平台，通过集成虚拟人、计算机视觉和对话式AI技术，为求职者提供最逼真的面试模拟体验。

## 🌟 核心特性

### 🎯 智能面试官
- **多类型面试**：行为面试、技术面试、情景面试
- **个性化提问**：基于职位描述(JD)的定制化问题
- **自然对话**：GPT-4驱动的智能对话系统

### 👁️ 视觉分析 (核心亮点)
- **眼神接触分析**：实时检测与面试官的眼神交流
- **面部表情识别**：评估自信度、紧张程度等情绪状态
- **姿态评估**：分析坐姿稳定性和肢体语言
- **实时反馈**：提供即时的非语言行为改进建议

### 📊 全方位反馈报告
- **内容分析**：STAR法则运用、关键词匹配、回答清晰度
- **沟通分析**：语速、填充词、情绪基调评估
- **视觉指标**：眼神接触时长、表情变化、姿态稳定性
- **可执行建议**：具体的练习和改进方案

## 🏗️ 技术架构

```
vita/
├── backend/              # FastAPI 后端服务
│   ├── core/            # 核心业务逻辑
│   ├── models/          # 数据模型
│   └── main.py          # 主应用入口
├── vision_service/      # 视觉分析微服务
│   ├── app.py           # MediaPipe + OpenCV
│   └── models/          # 视觉分析模型
├── frontend/            # React + TypeScript 前端
│   ├── src/
│   │   ├── components/  # React 组件
│   │   ├── store/       # Zustand 状态管理
│   │   └── api/         # API 客户端
│   └── package.json
└── docker-compose.yml   # 容器编排
```

### 技术栈

**后端**
- **FastAPI**: 高性能 Python Web 框架
- **Qwen & Llama模型**: 智能对话和反馈生成
- **Redis** + **aiocache**: 分布式缓存 & 会话存储
- **Prometheus**: 性能监控 & 指标采集
- **Pydantic**: 数据验证和序列化

**视觉分析**
- **MediaPipe**: Google 的机器学习管道框架
- **OpenCV**: 计算机视觉处理
- **NumPy**: 数值计算

**前端**
- **React 18 + TypeScript**: 现代化前端框架
- **Vite** + **Rollup**: 极速构建 & 智能代码分割
- **Zustand**: 轻量级状态管理
- **Tailwind CSS**: 实用优先的CSS框架
- **unplugin-icons** + **vite-plugin-imp**: 按需加载 & 体积优化
- **Axios**: HTTP 客户端

## 🚀 快速开始

### 前置条件
- Node.js 18+
- Python 3.11+
- Docker & Docker Compose
- Redis 6+（本地或容器，默认地址 `redis://localhost:6379/0`）
- （可选）Prometheus & Grafana 用于监控可视化
- Qwen API Key 或 Llama API Key

### 1. 克隆项目
```bash
git clone https://github.com/your-username/vita.git
cd vita
```

### 2. 环境配置
```bash
# 复制环境变量模板
cp env.example .env

# 编辑 .env 文件，添加你的 OpenAI API Key
# OpenAI配置已移除，现在使用本地Whisper + 本地TTS
```

### 3. 使用 Docker Compose 启动 (推荐)
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 4. 本地开发模式

#### 后端服务
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 视觉分析服务
```bash
cd vision_service
pip install -r requirements.txt
uvicorn app:app --reload --host 0.0.0.0 --port 8001
```

#### 前端服务
```bash
cd frontend
npm install
npm run dev
```

### 5. 访问应用
- **前端界面**: http://localhost:3000
- **后端 API 文档**: http://localhost:8000/docs
- **视觉分析 API**: http://localhost:8001/docs

## 📖 使用指南

### 基本流程
1. **设置面试**：输入职位描述，选择面试类型
2. **进行面试**：与AI面试官进行实时对话
3. **视觉分析**：系统自动分析您的表情、眼神和姿态
4. **获取反馈**：查看详细的分析报告和改进建议

### API 端点

#### 后端服务 (端口 8000)
- `POST /session/start` - 开始面试会话
- `POST /session/{id}/answer` - 提交答案
- `GET /session/{id}/feedback` - 获取反馈报告
- `GET /health` - 健康检查
- `GET /metrics` - Prometheus 性能指标

#### 视觉分析服务 (端口 8001)
- `POST /analyze` - 分析视频帧
- `GET /health` - 健康检查

## 🎯 产品规划

### Phase 1: MVP (当前版本)
- ✅ 基础面试对话系统
- ✅ 视觉分析核心功能
- ✅ 文字反馈报告
- ✅ 三种面试类型支持

### Phase 2: 增强功能
- 🔄 3D虚拟人面试官
- 🔄 语音识别和TTS
- 🔄 更丰富的视觉分析指标
- 🔄 行业专属题库

### Phase 3: 商业化
- 📋 B2B企业版
- 📋 高级数据分析
- 📋 人工教练服务
- 📋 API开放平台

## 🤝 贡献指南

我们欢迎各种形式的贡献！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交变更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系我们

- **邮箱**: contact@vita-ai.com
- **官网**: https://vita-ai.com
- **GitHub**: https://github.com/your-username/vita

## 🙏 技术栈与致谢

- **前端**: React, Vite, Three.js, shadcn/ui
- **后端**: FastAPI
- **AI 模型**: Qwen (通义千问), Llama
- **语音服务**: Whisper (本地), Edge-TTS (本地)

感谢所有开源社区的贡献。

---

**VITA** - 让每次面试都成为成长的机会 ✨ 

## 📈 性能监控与优化

- 后端集成 `async_timeit` 装饰器，自动采集 API 延迟 & 错误率
- 使用 **Redis** + **aiocache** 替换内存缓存，支持多实例扩展
- `/metrics` 端点导出标准 Prometheus 指标，可接入 Grafana 进行可视化
- 前端构建启用手动代码分割 + Gzip & Brotli 双重压缩，Bundle 体积减小 ~25%
- 新增 `PerformanceOptimizer` 组件，自动根据 FPS 调整 3D 渲染质量，保障 ≥45FPS

> 详细优化方案 & 性能对比请查看 [`__REMOVED_API_KEY__.md`](__REMOVED_API_KEY__.md) 