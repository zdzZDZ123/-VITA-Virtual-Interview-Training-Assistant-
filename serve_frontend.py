#!/usr/bin/env python3
"""
简单的前端静态文件服务器
用于测试前端页面
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

# 切换到前端构建目录
frontend_dist = Path("frontend/dist")
if not frontend_dist.exists():
    print(f"❌ 前端构建目录不存在: {frontend_dist.absolute()}")
    print("请先运行: cd frontend && npm run build")
    exit(1)

os.chdir(frontend_dist)
print(f"🗂️  服务目录: {frontend_dist.absolute()}")

# 配置服务器
PORT = 3000
Handler = http.server.SimpleHTTPRequestHandler

class CustomHandler(Handler):
    def end_headers(self):
        # 添加CORS头
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def guess_type(self, path):
        # 确保正确的MIME类型
        mimetype, encoding = super().guess_type(path)
        if path.endswith('.js'):
            return 'text/javascript', encoding
        elif path.endswith('.css'):
            return 'text/css', encoding
        return mimetype, encoding

try:
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        print(f"🚀 前端服务器启动成功!")
        print(f"🌐 地址: http://localhost:{PORT}")
        print(f"📁 文件列表:")
        for item in os.listdir("."):
            print(f"   - {item}")
        print("\n按 Ctrl+C 停止服务器")
        
        # 自动打开浏览器
        try:
            webbrowser.open(f"http://localhost:{PORT}")
        except:
            pass
            
        httpd.serve_forever()
        
except KeyboardInterrupt:
    print("\n👋 前端服务器已停止")
except Exception as e:
    print(f"❌ 服务器启动失败: {e}") 