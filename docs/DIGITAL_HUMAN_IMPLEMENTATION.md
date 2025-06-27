# VITA 数字人模块实现文档

## 概述

本文档记录了VITA项目中数字人模块第一阶段的实现，包括基础3D形象展示和核心口型同步功能。

## 实现内容

### 1. 技术栈选择

- **3D渲染引擎**: Three.js + React Three Fiber
- **动画系统**: 基于Three.js的动画循环和Blendshapes
- **口型同步**: 音频分析驱动的实时口型动画
- **前端框架**: React + TypeScript
- **样式**: Tailwind CSS

### 2. 核心组件

#### 2.1 DigitalHumanView (`frontend/src/components/digital-human/DigitalHumanView.tsx`)
- 主视图组件，负责3D场景的设置和渲染
- 处理音频播放和管理
- 提供灯光、相机和环境设置
- 支持音频URL和ArrayBuffer两种输入方式

#### 2.2 DigitalHumanModel (`frontend/src/components/digital-human/DigitalHumanModel.tsx`)
- 3D模型组件，当前使用简化的几何体构建基础形象
- 实现了以下动画功能：
  - 口型同步动画
  - 眨眼动画
  - 头部微动（idle状态）
  - 表情切换（smile, thinking等）
- 预留了加载真实3D模型的接口

#### 2.3 LipSyncController (`frontend/src/components/digital-human/LipSyncController.tsx`)
- 口型同步控制器类
- 音频分析功能：
  - 预分析：生成时间-口型映射表
  - 实时分析：通过Web Audio API分析音频频谱
- 提供getMouthShape方法获取当前时间的口型数据

#### 2.4 DigitalHumanInterviewRoom (`frontend/src/components/digital-human/DigitalHumanInterviewRoom.tsx`)
- 集成了数字人的完整面试室界面
- 左侧：数字人3D视图
- 右侧：对话界面和输入控件
- 支持文字和语音两种输入方式
- 自动管理数字人的表情和动作状态

#### 2.5 DigitalHumanDemo (`frontend/src/components/digital-human/DigitalHumanDemo.tsx`)
- 数字人功能演示页面
- 提供职位描述输入和面试类型选择
- 展示数字人特性和技术实现说明

### 3. 后端API扩展

在 `backend/main.py` 中添加了以下端点：

- `POST /api/session/{session_id}/start`: 开始数字人面试会话
- `POST /api/session/{session_id}/answer`: 提交答案给数字人
- `POST /api/speech/transcribe`: 支持base64格式的语音转文字

这些API返回包含以下信息：
- 面试问题文本
- 语音数据（base64格式）
- 数字人表情提示
- 数字人动作提示

### 4. 动画系统

#### 4.1 口型同步
- 基于音频振幅分析
- 20ms窗口采样
- 平滑过渡（lerp插值）
- 支持预分析和实时分析两种模式

#### 4.2 表情系统
- neutral（中性）
- smile（微笑）
- thinking（思考）
- curious（好奇）
- serious（严肃）
- listening（倾听）

#### 4.3 动作系统
- idle（待机）
- talking（说话）
- listening（倾听）
- nodding（点头）
- greeting（问候）

### 5. 集成方式

1. 在App.tsx中添加了数字人路由
2. 在InterviewSetup组件中添加了"开始数字人面试"按钮
3. 使用Zustand store管理会话状态

## 使用方法

### 安装依赖

```bash
cd frontend
npm install
```

新增的依赖包：
- three: 3D图形库
- @react-three/fiber: React的Three.js绑定
- @react-three/drei: React Three Fiber的辅助组件库

### 启动服务

1. 启动后端服务：
```bash
cd backend
python run_backend.py
```

2. 启动前端服务：
```bash
cd frontend
npm run dev
```

3. 访问应用并点击"开始数字人面试"

## 当前实现的特性

1. ✅ 基础3D形象展示
2. ✅ 口型同步（基于音频振幅）
3. ✅ 基础表情切换
4. ✅ 眨眼动画
5. ✅ 头部微动动画
6. ✅ 与TTS语音集成
7. ✅ 支持语音输入（STT）
8. ✅ 完整的面试对话流程

## 后续优化建议

### 第二阶段：丰富表情与预设动作
1. 制作更多表情动画
2. 添加手势动画
3. 实现更自然的过渡动画
4. 优化口型同步算法（考虑音素分析）

### 第三阶段：高级功能
1. 加载真实的3D模型（GLTF/GLB格式）
2. 实现基于AI的表情生成
3. 添加眼神追踪
4. 实现更复杂的肢体语言
5. 性能优化（LOD、纹理压缩等）

## 技术挑战与解决方案

1. **口型同步延迟**
   - 问题：音频播放与口型动画不同步
   - 解决：预分析音频生成时间映射表

2. **3D渲染性能**
   - 问题：复杂模型可能导致性能问题
   - 解决：使用简化几何体，优化渲染循环

3. **跨浏览器兼容性**
   - 问题：Web Audio API在不同浏览器表现不一
   - 解决：添加兼容性检查和降级方案

## 总结

第一阶段成功实现了数字人的基础功能，包括3D形象展示、口型同步和基础动画。系统架构具有良好的扩展性，为后续增强功能奠定了基础。当前实现已经能够提供基本的数字人面试体验，用户可以看到一个会说话、有表情的3D虚拟面试官。 