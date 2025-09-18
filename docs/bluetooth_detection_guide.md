# 检测设备是否支持蓝牙的完整指南

## 1. 安装必要的工具

### Ubuntu/Debian
```bash
sudo apt install bluez bluez-utils
```

### CentOS/RHEL/Fedora
```bash
sudo yum install bluez bluez-utils
# 或者在较新版本
sudo dnf install bluez bluez-utils
```

### Arch Linux
```bash
sudo pacman -S bluez bluez-utils
```

## 2. 检测命令（按推荐顺序）

### 2.1 检查蓝牙硬件接口
```bash
hciconfig -a
```
**说明**：最直接的方法，显示所有蓝牙控制器的详细信息
- 如果有输出，说明系统检测到蓝牙硬件
- 显示设备状态（UP RUNNING）、MAC地址、支持的功能等

### 2.2 检查蓝牙控制器信息
```bash
bluetoothctl show
```
**说明**：显示蓝牙控制器的详细配置和支持的服务

### 2.3 检查蓝牙服务状态
```bash
systemctl status bluetooth
```
**说明**：检查蓝牙服务是否正在运行

### 2.4 检查内核模块
```bash
lsmod | grep bluetooth
```
**说明**：查看是否加载了蓝牙相关的内核模块

### 2.5 查看内核日志
```bash
sudo dmesg | grep -i bluetooth
```
**说明**：查看系统启动时的蓝牙设备识别信息

## 3. 硬件检测命令

### 3.1 USB蓝牙设备
```bash
# 查找蓝牙关键词
lsusb | grep -i bluetooth

# 查找制造商（如MediaTek）
lsusb | grep -i mediatek

# 查找无线设备
lsusb | grep -i wireless

# 查看所有USB设备
lsusb
```

### 3.2 PCIe蓝牙设备
```bash
lspci | grep -i bluetooth
```

## 4. 判断标准

### ✅ 设备支持蓝牙的标志：
- `hciconfig -a` 有输出显示 hci0 等设备
- `bluetoothctl show` 显示控制器信息
- `lsmod | grep bluetooth` 显示已加载的蓝牙模块
- `systemctl status bluetooth` 显示服务运行状态

### ❌ 设备不支持蓝牙的标志：
- `hciconfig -a` 无输出或提示 "No such device"
- `bluetoothctl show` 提示 "No default controller available"
- 无蓝牙相关内核模块加载

## 5. 常见问题

### Q: lsusb/lspci 找不到蓝牙设备？
A: 这很正常，原因可能是：
- 厂商名称不包含"bluetooth"关键词
- 集成在WiFi芯片中显示为无线设备
- 只要 `hciconfig` 和 `bluetoothctl` 能正常工作即可

### Q: 蓝牙服务未运行？
A: 启动蓝牙服务：
```bash
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
```

### Q: 权限问题？
A: 将用户添加到蓝牙组：
```bash
sudo usermod -a -G bluetooth $USER
```
然后重新登录。

## 6. 示例输出

### 正常工作的蓝牙设备输出示例：
```bash
$ hciconfig -a
hci0:   Type: Primary  Bus: USB
        BD Address: F8:3D:C6:AA:7D:75  ACL MTU: 1021:6
        UP RUNNING
        RX bytes:1874 acl:0 sco:0 events:154 errors:0
        TX bytes:6795 acl:0 sco:0 commands:154 errors:0
        ...
```

```bash
$ lsmod | grep bluetooth
bluetooth    1015808  34 btrtl,btmtk,btintel,btbcm,bnep,btusb,rfcomm
```

这表明设备完全支持蓝牙功能。