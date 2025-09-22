# BLE设备模拟器实现方案

## 项目概述

本文档描述了在现有BLE Simulator项目中添加BLE Peripheral（外围设备）模式的完整实现方案。该功能将使Linux主机能够模拟成一个辅助架BLE设备，向连接的手机客户端（如nRF Connect）发送握力数据。

## 需求分析

### 功能需求
1. **设备模拟**：将Linux主机模拟为"辅助架"BLE设备
2. **数据传输**：向连接的客户端发送握力数据
3. **Web界面**：在现有web界面中添加"BLE设备模拟器"功能
4. **数据格式**：`L1:123 L2:111 L3:100 R1:145 R2:555 R3:120 Score:85`

### 技术需求
1. **GATT服务器**：实现BLE GATT服务器功能
2. **广播支持**：设备可被其他设备发现和连接
3. **特征值管理**：定义握力数据的特征值和描述符
4. **实时数据更新**：支持握力数据的实时传输

## 系统架构

### 整体架构
```
Web前端 ← HTTP API → FastAPI/Flask → BLE Peripheral Service → BlueZ D-Bus API
```

### 核心组件

#### 1. BLE Peripheral服务层
- **文件位置**：`src/python/service/ble_peripheral_service.py`
- **功能**：管理BLE Peripheral模式的启动、停止和数据传输

#### 2. GATT服务器实现
- **文件位置**：`src/python/service/bluetooth/gatt_server.py`
- **功能**：实现BLE GATT服务器，定义服务和特征值

#### 3. 广播管理器
- **文件位置**：`src/python/service/bluetooth/advertisement.py`
- **功能**：管理BLE设备广播，使设备可被发现

#### 4. 握力数据模拟器
- **文件位置**：`src/python/service/bluetooth/grip_simulator.py`
- **功能**：生成和管理握力数据

## 技术实现方案

### BLE GATT服务定义

#### 辅助架服务 (Support Frame Service)
- **服务UUID**：`12345678-1234-5678-9abc-123456789abc`
- **服务名称**：Support Frame Service

#### 特征值定义

1. **握力数据特征值 (Grip Data Characteristic)**
   - **UUID**：`12345678-1234-5678-9abc-123456789abd`
   - **属性**：Read, Notify
   - **数据格式**：UTF-8字符串
   - **数据示例**：`L1:123 L2:111 L3:100 R1:145 R2:555 R3:120 Score:85`

2. **设备信息特征值 (Device Info Characteristic)**
   - **UUID**：`12345678-1234-5678-9abc-123456789abe`
   - **属性**：Read
   - **数据内容**：设备型号、版本等信息

3. **控制特征值 (Control Characteristic)**
   - **UUID**：`12345678-1234-5678-9abc-123456789abf`
   - **属性**：Write
   - **功能**：接收客户端控制命令（开始/停止数据传输等）

### 数据传输机制

#### 数据格式说明
```
握力数据格式：L1:123 L2:111 L3:100 R1:145 R2:555 R3:120 Score:85

说明：
- L1,L2,L3：左手扶手三个传感器的握力值
- R1,R2,R3：右手扶手三个传感器的握力值
- Score：综合评分
- 数值范围：0-999
- 更新频率：每秒1-2次
```

#### 传输模式
1. **主动推送**：使用BLE Notify机制主动向客户端推送数据
2. **按需读取**：客户端可通过Read操作获取当前数据
3. **实时更新**：数据更新频率为1-2Hz

## 代码实现结构

### 目录结构
```
src/python/
├── service/
│   ├── ble_peripheral_service.py       # BLE Peripheral业务服务
│   └── bluetooth/
│       ├── gatt_server.py              # GATT服务器实现
│       ├── advertisement.py            # 广播管理
│       └── grip_simulator.py           # 握力数据模拟
├── app/
│   ├── fastapi_app/routers/
│   │   └── peripheral_api.py           # Peripheral API路由
│   └── flask_app/blueprints/
│       └── peripheral_bp.py            # Peripheral Web界面
└── templates/
    └── peripheral/
        └── simulator.html              # 设备模拟器页面
```

### 依赖库要求
```python
# requirements.txt 新增依赖
pydbus>=0.6.0           # D-Bus通信
pygobject>=3.36.0       # GLib事件循环
dbus-python>=1.2.16     # Python D-Bus绑定
```

## Web界面设计

### 界面布局
1. **主页新增按钮**：在index.html的主要按钮区域添加"BLE设备模拟器"按钮
2. **模拟器页面**：新建独立页面显示设备状态和数据
3. **状态监控**：实时显示设备广播状态、连接状态、数据传输状态

### 功能特性
1. **启动/停止模拟器**：一键启动或停止BLE设备模拟
2. **实时数据显示**：显示当前发送的握力数据
3. **连接状态监控**：显示连接的客户端设备信息
4. **数据传输日志**：记录数据传输历史

## API接口设计

### Peripheral控制API
```http
POST /api/v1/peripheral/start
POST /api/v1/peripheral/stop
GET  /api/v1/peripheral/status
GET  /api/v1/peripheral/data
POST /api/v1/peripheral/data
```

### 数据模型
```python
class PeripheralStatus:
    is_running: bool
    is_advertising: bool
    connected_clients: List[str]
    current_data: str

class GripData:
    left_sensors: List[int]    # L1, L2, L3
    right_sensors: List[int]   # R1, R2, R3
    score: int
```

## 开发计划

### 阶段1：核心功能实现 (2-3天)
1. 实现GATT服务器基础框架
2. 实现设备广播功能
3. 定义握力数据服务和特征值
4. 基础数据传输测试

### 阶段2：业务逻辑完善 (2天)
1. 实现握力数据模拟器
2. 完善数据传输机制
3. 添加错误处理和日志
4. 性能优化

### 阶段3：Web界面开发 (1-2天)
1. 添加API接口
2. 实现前端界面
3. 状态监控和数据展示
4. 用户体验优化

### 阶段4：测试和部署 (1天)
1. 功能测试
2. 与nRF Connect的兼容性测试
3. 文档更新
4. Docker镜像更新

## 测试方案

### 单元测试
- GATT服务器功能测试
- 数据模拟器测试
- API接口测试

### 集成测试
- BlueZ集成测试
- Web界面功能测试
- 端到端数据传输测试

### 兼容性测试
- nRF Connect连接测试
- Android/iOS设备兼容性测试
- 多客户端连接测试

## 部署要求

### 系统依赖
- Ubuntu 18.04+
- BlueZ 5.50+
- Python 3.8+
- D-Bus系统服务

### 权限要求
- 蓝牙设备访问权限
- D-Bus系统总线访问权限
- NET_ADMIN capabilities（Docker环境）

### 配置文件
```yaml
# config/peripheral.yml
peripheral:
  device_name: "Support Frame Simulator"
  manufacturer_name: "BLE Simulator Inc"
  model_number: "SF-001"
  data_update_interval: 1.0  # 秒
  max_clients: 5
```

## 预期效果

实现后，用户可以：
1. 在Web界面点击"BLE设备模拟器"启动模拟器
2. 使用手机nRF Connect扫描并连接到"Support Frame Simulator"设备
3. 订阅握力数据特征值，实时接收模拟的握力数据
4. 通过Web界面监控连接状态和数据传输情况

## 风险评估

### 技术风险
- BlueZ版本兼容性问题
- D-Bus权限配置复杂性
- 多客户端连接稳定性

### 缓解措施
- 详细的环境检测和错误提示
- 完善的日志记录和调试信息
- 优雅的错误处理和恢复机制

## 总结

该实现方案提供了完整的BLE Peripheral模式功能，能够满足用户在手机上通过nRF Connect连接并接收握力数据的需求。通过模块化的设计和清晰的接口定义，确保了代码的可维护性和可扩展性。