# BLE Simulator Docker Compose 部署指南

## 使用方法

### 1. 启动容器
```bash
cd deploy
podman-compose up -d
```

### 2. 进入容器
```bash
podman-compose exec ble-simulator bash
```

### 3. 在容器内安装必要软件
```bash
# 更新包列表
apt update

# 安装Python和蓝牙工具
apt install -y python3 python3-pip python3-venv
apt install -y bluez bluez-tools libbluetooth-dev pkg-config build-essential

# 安装Python蓝牙库
pip3 install bleak pybluez

# 验证蓝牙功能
hciconfig -a
bluetoothctl show
```

### 4. 停止容器
```bash
podman-compose down
```

## 配置说明

### 蓝牙访问配置
- `privileged: true` - 提供特权模式访问硬件
- `network_mode: host` - 使用主机网络栈
- `devices` - 映射蓝牙设备到容器
- `volumes` - 映射USB总线信息

### 工作目录
- 项目目录映射到容器的 `/app` 目录
- 工作目录设置为 `/app`

### 环境变量
- `TERM=xterm-256color` - 支持彩色终端

## 故障排除

### 蓝牙设备不可用
1. 确保主机蓝牙服务运行：
   ```bash
   sudo systemctl status bluetooth
   ```

2. 检查设备权限：
   ```bash
   ls -la /dev/rfcomm* /dev/ttyUSB*
   ```

3. 如果设备不存在，移除对应的devices配置行

### 权限问题
容器运行在特权模式下，应该有足够权限访问蓝牙硬件。

## 开发工作流
1. 启动容器：`podman-compose up -d`
2. 进入容器：`podman-compose exec ble-simulator bash`
3. 开发和测试您的BLE模拟器代码
4. 代码变更会自动同步到容器内（通过volume映射）