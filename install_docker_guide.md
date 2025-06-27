# Docker Desktop 安装指南

## 方法1：手动下载安装（推荐）

1. 使用浏览器访问以下地址下载Docker Desktop：
   - 官方地址：https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe
   - 或者访问：https://www.docker.com/products/docker-desktop/

2. 下载完成后，将安装程序保存到 `D:\docker_install\` 目录

3. 以管理员身份运行安装程序

## 方法2：使用包管理器（如果可用）

如果系统安装了 Chocolatey：
```powershell
choco install docker-desktop
```

如果系统安装了 Winget：
```powershell
winget install Docker.DockerDesktop
```

## 安装后配置

1. 启动 Docker Desktop
2. 完成初始设置
3. 在设置中配置镜像源（可选，提升下载速度）：
   ```json
   {
     "registry-mirrors": [
       "https://docker.mirrors.ustc.edu.cn",
       "https://hub-mirror.c.163.com"
     ]
   }
   ```

## 验证安装

安装完成后，在PowerShell中运行：
```powershell
docker --version
docker-compose --version
```

## 运行VITA项目

安装Docker完成后，在VITA项目目录运行：
```powershell
docker-compose up --build
```

这将构建并启动前端和后端服务。 