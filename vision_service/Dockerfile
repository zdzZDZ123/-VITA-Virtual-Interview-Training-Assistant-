FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖 (OpenCV 和 MediaPipe 需要)
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    libgtk-3-0 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8001

# 启动命令
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]