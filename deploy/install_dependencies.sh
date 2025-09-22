#!/bin/bash

# BLE Simulator 系统依赖安装脚本
# 适用于 Ubuntu/Debian 系统

set -e

echo "🔧 安装 BLE Simulator 系统依赖..."

# 更新包列表
echo "📦 更新包列表..."
sudo apt update

# 安装 Python 开发工具
echo "🐍 安装 Python 开发工具..."
sudo apt install -y \
    python3-dev \
    python3-pip \
    python3-venv \
    build-essential

# 安装 BlueZ 和蓝牙开发库
echo "📡 安装 BlueZ 和蓝牙开发库..."
sudo apt install -y \
    bluez \
    bluez-tools \
    libbluetooth-dev \
    bluetooth

# 安装 GObject 和 D-Bus 开发库 (pygobject 依赖)
echo "🔗 安装 GObject 和 D-Bus 开发库..."
sudo apt install -y \
    libgirepository1.0-dev \
    libgirepository-2.0-dev \
    libcairo2-dev \
    libglib2.0-dev \
    gobject-introspection \
    libgirepository-1.0-1 \
    gir1.2-glib-2.0 \
    libffi-dev

# 安装 D-Bus 相关库
echo "🚌 安装 D-Bus 开发库..."
sudo apt install -y \
    libdbus-1-dev \
    libdbus-glib-1-dev \
    dbus

# 安装 pkg-config 和构建工具
echo "🛠️ 安装构建工具..."
sudo apt install -y \
    pkg-config \
    cmake \
    meson \
    ninja-build

# 可选：安装系统级 Python 包 (推荐方式)
echo "📚 安装系统级 Python 蓝牙库..."
sudo apt install -y \
    python3-gi \
    python3-gi-cairo \
    python3-dbus \
    python3-bluez

echo "✅ 系统依赖安装完成！"
echo ""
echo "🔧 现在可以安装 Python 依赖："
echo "   cd /path/to/ble_simulator"
echo "   python3 -m venv .venv"
echo "   source .venv/bin/activate"
echo "   pip install -r deploy/requirements.txt"
echo ""
echo "📋 验证蓝牙状态："
echo "   sudo systemctl status bluetooth"
echo "   bluetoothctl show"
echo ""
echo "⚠️  注意：运行 BLE 模拟器可能需要 root 权限或添加用户到 bluetooth 组："
echo "   sudo usermod -a -G bluetooth \$USER"
echo "   # 然后重新登录"