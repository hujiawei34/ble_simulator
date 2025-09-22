# BLE Simulator 安装指南

本文档提供了 BLE Simulator 项目的详细安装指南，包括系统依赖、Python 依赖和可能遇到的问题解决方案。

## 系统要求

- **操作系统**: Ubuntu 18.04+ / Debian 10+
- **Python**: 3.8+
- **蓝牙硬件**: 支持 BLE 的蓝牙适配器
- **权限**: 需要访问蓝牙设备和 D-Bus 系统总线

## 快速安装

### 1. 安装系统依赖

运行我们提供的安装脚本：

```bash
# 进入项目目录
cd /path/to/ble_simulator

# 运行系统依赖安装脚本
sudo bash deploy/install_dependencies.sh
```

### 2. 安装 Python 依赖

```bash
# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate

# 安装 Python 依赖
pip install -r deploy/requirements.txt
```

### 3. 配置权限

```bash
# 将用户添加到 bluetooth 组
sudo usermod -a -G bluetooth $USER

# 重新登录或重启以使权限生效
# 或者临时获取权限：
newgrp bluetooth
```

## 分步安装指南

### 步骤 1: 系统级依赖

#### Python 开发环境
```bash
sudo apt update
sudo apt install -y python3-dev python3-pip python3-venv build-essential
```

#### BlueZ 蓝牙栈
```bash
sudo apt install -y bluez bluez-tools libbluetooth-dev bluetooth
```

#### GObject 和 D-Bus 开发库
```bash
sudo apt install -y \
    libgirepository1.0-dev \
    libcairo2-dev \
    libglib2.0-dev \
    libgobject-introspection-1.0-0 \
    gobject-introspection \
    gir1.2-glib-2.0
```

#### D-Bus 库
```bash
sudo apt install -y libdbus-1-dev libdbus-glib-1-dev dbus
```

#### 构建工具
```bash
sudo apt install -y pkg-config cmake meson ninja-build
```

### 步骤 2: Python 虚拟环境

```bash
# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate

# 升级 pip
pip install --upgrade pip setuptools wheel
```

### 步骤 3: Python 依赖安装

有两种方式安装 Python 依赖：

#### 方式 1: 直接安装 (推荐)
```bash
pip install -r deploy/requirements.txt
```

#### 方式 2: 使用系统包 (如果方式1失败)
```bash
# 安装系统级 Python 包
sudo apt install -y python3-gi python3-gi-cairo python3-dbus python3-bluez

# 安装其他依赖
pip install -r deploy/requirements-minimal.txt

# 创建符号链接到虚拟环境
ln -s /usr/lib/python3/dist-packages/gi .venv/lib/python3.*/site-packages/
ln -s /usr/lib/python3/dist-packages/dbus .venv/lib/python3.*/site-packages/
ln -s /usr/lib/python3/dist-packages/_dbus_bindings.cpython-*.so .venv/lib/python3.*/site-packages/
```

## 功能模块说明

项目包含两个主要功能模块：

### BLE Central 模式 (默认功能)
- **功能**: 扫描和连接其他 BLE 设备
- **依赖**: 只需要 `bleak` 库
- **安装**: `pip install -r deploy/requirements-minimal.txt`

### BLE Peripheral 模式 (模拟器功能)
- **功能**: 将本机模拟为 BLE 设备
- **依赖**: 需要 `pygobject`, `pydbus`, `dbus-python`
- **安装**: 需要先安装系统依赖，然后 `pip install -r deploy/requirements.txt`

## 验证安装

### 1. 验证蓝牙服务
```bash
# 检查蓝牙服务状态
sudo systemctl status bluetooth

# 检查蓝牙适配器
bluetoothctl show

# 检查用户权限
groups $USER | grep bluetooth
```

### 2. 验证 Python 依赖
```bash
# 激活虚拟环境
source .venv/bin/activate

# 测试基础功能
python -c "import bleak; print('BLE Central 功能可用')"

# 测试模拟器功能 (如果安装了完整依赖)
python -c "import gi, dbus, pydbus; print('BLE Peripheral 功能可用')"
```

### 3. 启动服务
```bash
# 激活虚拟环境
source .venv/bin/activate

# 启动服务
python src/python/run_server.py
```

访问 http://localhost:8000 查看 Web 界面。

## 常见问题解决

### 问题 1: pygobject 安装失败

**错误信息**: `error: Microsoft Visual C++ 14.0 is required` 或 `Dependency 'girepository-2.0' is required but not found`

**解决方案**:
```bash
# 安装系统依赖
sudo apt install -y libgirepository1.0-dev libgirepository-2.0-dev libcairo2-dev pkg-config 

# 或使用系统包
sudo apt install -y python3-gi
```

### 问题 2: 蓝牙权限问题

**错误信息**: `Permission denied` 或 `org.freedesktop.DBus.Error.AccessDenied`

**解决方案**:
```bash
# 添加用户到 bluetooth 组
sudo usermod -a -G bluetooth $USER

# 重新登录或运行
newgrp bluetooth

# 检查 D-Bus 权限
ls -la /var/run/dbus/system_bus_socket
```

### 问题 3: D-Bus 连接失败

**错误信息**: `dbus.exceptions.DBusException: org.freedesktop.DBus.Error.FileNotFound`

**解决方案**:
```bash
# 重启 D-Bus 服务
sudo systemctl restart dbus

# 检查 BlueZ 服务
sudo systemctl restart bluetooth
sudo systemctl enable bluetooth
```

### 问题 4: BlueZ 版本不兼容

**错误信息**: `No such interface 'org.bluez.LEAdvertisingManager1'`

**解决方案**:
```bash
# 检查 BlueZ 版本
bluetoothctl version

# 如果版本 < 5.50，需要升级
sudo apt install -y bluez/focal-backports  # Ubuntu 20.04
# 或编译最新版本
```

## Docker 部署

不支持docker部署

## 开发环境设置

### 代码编辑器配置

在 VSCode 中，添加以下配置到 `.vscode/settings.json`：

```json
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true
}
```

### 环境变量

创建 `.env` 文件：

```env
# 开发环境配置
DEBUG=true
LOG_LEVEL=DEBUG
HOST=0.0.0.0
PORT=8000

# 蓝牙适配器
BLUETOOTH_ADAPTER=/org/bluez/hci0
```

## 支持与反馈

如果遇到安装问题：

1. 检查系统版本和硬件兼容性
2. 查看日志文件 `logs/` 目录
3. 在项目 Issue 中搜索类似问题
4. 提交新的 Issue 并附上错误日志

## 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。