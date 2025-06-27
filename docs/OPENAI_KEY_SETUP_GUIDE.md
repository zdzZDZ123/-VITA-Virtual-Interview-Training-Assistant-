# OpenAI API密钥配置指南

## 配置完成！

您的OpenAI API密钥已经配置完成。以下是详细信息：

### 1. 配置的更改

#### 启动脚本
创建了 `start_with_openai_key.bat`，包含以下环境变量：
- `OPENAI_API_KEY`: 您提供的OpenAI密钥（用于语音服务）
- `LLAMA_API_KEY`: Llama模型服务密钥
- `QWEN_API_KEY`: Qwen备用服务密钥

#### 代码更新
1. **config.py**：恢复了OpenAI API密钥的支持
2. **speech.py**：优化了语音服务，优先使用OpenAI进行TTS和STT

### 2. 使用方法

#### 方法一：使用启动脚本（推荐）
```bash
# 双击运行或在命令行执行
start_with_openai_key.bat
```

#### 方法二：手动设置环境变量
```bash
# Windows命令行
set OPENAI_API_KEY=YOUR_API_KEY

# 启动后端
cd backend
python main.py

# 新开一个终端，启动前端
cd frontend
npm run dev
```

#### 方法三：创建.env文件（需要手动创建）
在项目根目录创建`.env`文件：
```env
OPENAI_API_KEY="__REMOVED_API_KEY__"  # 替换为你的真实密钥
```

### 3. 语音功能现在支持

有了OpenAI API密钥，以下语音功能将正常工作：

1. **文字转语音（TTS）**
   - 使用OpenAI的TTS模型
   - 支持多种语音选项（nova, alloy, echo等）
   - 可调节语速

2. **语音识别（STT）**
   - 使用OpenAI的Whisper模型
   - 支持中文识别
   - 高准确率

3. **实时语音对话**
   - WebSocket实时通信
   - 流式语音合成
   - 低延迟交互

### 4. 测试语音功能

1. 启动服务后，访问：http://localhost:5173
2. 进入面试页面
3. 开启"语音交互模式"
4. 点击"初始化音频"（如果需要）
5. 测试播放问题和录音回答

### 5. 故障排除

如果语音功能仍有问题：

1. **检查控制台日志**
   - 查看是否有"OpenAI API密钥验证成功"的消息
   - 检查是否有网络错误

2. **验证API密钥**
   - 确保密钥没有过期
   - 检查密钥的使用限额

3. **浏览器兼容性**
   - 使用Chrome、Firefox或Edge浏览器
   - 允许网站访问麦克风

4. **网络连接**
   - 确保能访问OpenAI API
   - 检查防火墙设置

### 6. 安全提醒

⚠️ **重要**：不要将包含API密钥的文件提交到Git仓库！
- `.env`文件应该在`.gitignore`中
- 启动脚本仅供本地使用
- 生产环境应使用环境变量或密钥管理服务

### 7. 后续优化建议

1. **缓存优化**：对常用语音进行缓存，减少API调用
2. **错误处理**：增强网络错误的重试机制
3. **用户体验**：添加语音波形可视化
4. **多语言支持**：扩展到英语等其他语言

## 总结

OpenAI API密钥已成功配置，语音面试功能应该可以正常使用了。使用`start_with_openai_key.bat`启动服务即可开始测试。

如有任何问题，请查看控制台日志或参考故障排除部分。

### 第三步：验证密钥

运行测试脚本以确保你的API密钥是有效的：

```bash
python backend/test_api.py
```

如果看到 "✅ API connection successful!" 字样，说明配置成功！

## 常见问题

**Q: 我没有OpenAI账户怎么办?**
A: 你需要访问 [OpenAI官网](https://platform.openai.com/signup) 注册一个账户。

**Q: 密钥有免费额度吗?**
A: 新用户通常会有一小笔免费试用额度。你可以在OpenAI的[账户用量页面](https://platform.openai.com/account/usage)查看。

**Q: 我应该把密钥告诉别人吗?**
A: **绝对不要！** API密钥等同于你的密码，泄露它会导致你的账户被盗用。

**安全提醒：请勿将包含API密钥的任何代码或文件上传到公共GitHub仓库。** 