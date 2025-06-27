# Windows 上安装 FFmpeg

## 方法1：使用 Scoop（推荐）

1. 安装 Scoop（如果还没有安装）：
```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
irm get.scoop.sh | iex
```

2. 安装 FFmpeg：
```powershell
scoop install ffmpeg
```

## 方法2：手动安装

1. 下载 FFmpeg
   - 访问：https://www.gyan.dev/ffmpeg/builds/
   - 下载 "release builds" 中的 "full" 版本

2. 解压到合适的位置，例如：`C:\ffmpeg`

3. 添加到系统 PATH：
   - 打开"系统属性" → "高级" → "环境变量"
   - 在"系统变量"中找到 Path，点击"编辑"
   - 添加：`C:\ffmpeg\bin`
   - 确定保存

4. 重启命令行窗口

## 验证安装

运行以下命令验证：
```bash
ffmpeg -version
```

如果显示版本信息，说明安装成功。 