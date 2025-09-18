# Ubuntu安装Podman完整指导

## 1. 配置Ubuntu APT源（推荐）

在安装Podman之前，建议先配置国内APT源以提升下载速度。

### 1.1 检查Ubuntu版本
```bash
lsb_release -c
```

### 1.2 备份原始源列表
```bash
sudo cp /etc/apt/sources.list /etc/apt/sources.list.backup
```

### 1.3 配置阿里云APT源
```bash
# 编辑源配置文件
sudo nano /etc/apt/sources.list
```

根据您的Ubuntu版本，替换为相应的阿里云源：

**Ubuntu 24.10 (plucky)**：
```bash
deb http://mirrors.aliyun.com/ubuntu/ plucky main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ plucky-security main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ plucky-updates main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ plucky-backports main restricted universe multiverse
```

**Ubuntu 22.04 LTS (jammy)**：
```bash
deb http://mirrors.aliyun.com/ubuntu/ jammy main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ jammy-security main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ jammy-updates main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ jammy-backports main restricted universe multiverse
```

**Ubuntu 20.04 LTS (focal)**：
```bash
deb http://mirrors.aliyun.com/ubuntu/ focal main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ focal-security main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ focal-updates main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ focal-backports main restricted universe multiverse
```

### 1.4 更新软件包列表
```bash
sudo apt update
```

## 2. 安装Podman

### 方法一：通过apt安装（推荐）
```bash
# 更新包列表
sudo apt update

# 安装podman
sudo apt install podman

# 验证安装
podman --version
```

### 方法二：通过官方仓库安装（最新版本）
```bash
# 添加官方仓库
echo "deb https://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable/xUbuntu_$(lsb_release -rs)/ /" | sudo tee /etc/apt/sources.list.d/devel:kubic:libcontainers:stable.list

# 添加GPG密钥
curl -fsSL https://download.opensuse.org/repositories/devel:kubic:libcontainers:stable/xUbuntu_$(lsb_release -rs)/Release.key | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/devel_kubic_libcontainers_stable.gpg > /dev/null

# 更新并安装
sudo apt update
sudo apt install podman
```

## 3. 配置阿里云镜像源

### 3.1 备份原始配置（如果存在）
```bash
sudo cp /etc/containers/registries.conf /etc/containers/registries.conf.backup 2>/dev/null || true
```

### 3.2 创建新的配置文件
```bash
# 创建配置目录（如果不存在）
sudo mkdir -p /etc/containers

# 编辑配置文件
sudo nano /etc/containers/registries.conf
```

### 3.3 配置内容
将以下内容写入 `/etc/containers/registries.conf`：

```toml
# 纯 v2 格式配置
unqualified-search-registries = ["docker.io", "quay.io"]

[[registry]]
prefix = "docker.io"
location = "docker.io"

[[registry.mirror]]
location = "registry.cn-hangzhou.aliyuncs.com"

[[registry.mirror]]
location = "registry.cn-shanghai.aliyuncs.com"

[[registry.mirror]]
location = "registry.cn-beijing.aliyuncs.com"

[[registry]]
prefix = "quay.io"
location = "quay.io"

[[registry.mirror]]
location = "quay.mirrors.ustc.edu.cn"
```

## 4. 验证配置

```bash
# 测试拉取镜像
sudo podman pull hello-world

# 查看配置信息
podman info | grep -A 10 registries

# 测试其他常用镜像
podman pull nginx
podman pull ubuntu:22.04
```

## 5. 安装后配置（可选）

### 5.1 启用用户命名空间
```bash
# 如果遇到权限问题，可以启用用户命名空间
echo 'user.max_user_namespaces=28633' | sudo tee -a /etc/sysctl.d/userns.conf

# 重新加载sysctl配置
sudo sysctl --system
```

### 5.2 用户级配置（可选）
```bash
# 创建用户配置目录
mkdir -p ~/.config/containers

# 复制配置到用户目录
cp /etc/containers/registries.conf ~/.config/containers/registries.conf
```

## 6. 常见问题及解决方案

### 6.1 配置格式错误
**错误信息**：`mixing sysregistry v1/v2 is not supported`

**解决方案**：
- 确保使用纯 v2 格式配置
- 使用 `unqualified-search-registries` 而不是 `[registries.search]`
- 避免混合 v1 和 v2 语法

### 6.2 权限问题
```bash
# 将用户添加到相关组
sudo usermod -a -G containers $USER

# 重新登录生效
```

### 6.3 网络连接问题
```bash
# 如果镜像拉取失败，可以尝试不同的镜像源
# 或者临时使用原始仓库
podman pull docker.io/hello-world
```

## 7. Podman与Docker的兼容性

### 7.1 命令别名（可选）
```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
echo 'alias docker=podman' >> ~/.bashrc
source ~/.bashrc
```

### 7.2 兼容性说明
- Podman完全兼容Docker Hub镜像
- 支持Dockerfile构建
- 命令语法与Docker高度相似
- 无需守护进程，更安全

## 8. 测试命令

```bash
# 基本测试
podman run hello-world

# 运行交互式容器
podman run -it ubuntu:22.04 /bin/bash

# 后台运行服务
podman run -d -p 8080:80 nginx

# 查看运行的容器
podman ps

# 停止容器
podman stop <container_id>
```

## 9. 故障排除

### 9.1 清除配置重新开始
```bash
# 删除配置文件
sudo rm /etc/containers/registries.conf

# 重新安装podman
sudo apt remove podman
sudo apt install podman
```

### 9.2 查看详细日志
```bash
# 查看详细拉取日志
podman pull --log-level=debug <image_name>

# 查看系统信息
podman system info
```

### 9.3 恢复备份配置
```bash
# 如果有备份，可以恢复
sudo cp /etc/containers/registries.conf.backup /etc/containers/registries.conf
```

配置完成后，Podman将优先使用阿里云镜像源，大大提升容器镜像的下载速度。