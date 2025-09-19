# BLE Simulator Flask + FastAPI 应用

这是一个基于 Flask 和 FastAPI 的混合 Web 应用，用于蓝牙低功耗 (BLE) 设备的模拟和管理。

## 快速开始

### 1. 安装依赖
```bash
cd ../../deploy
pip install -r requirements.txt
```

### 2. 启动应用
```bash
cd ../src/python
python run_server.py
```

或者直接运行：
```bash
python -m app.main
```

### 3. 访问应用
- Web界面: http://localhost:8000/
- API文档: http://localhost:8000/api/docs
- ReDoc文档: http://localhost:8000/api/redoc

## 项目结构

```
src/python/
├── app/                    # 主应用目录
│   ├── config.py          # 配置管理
│   ├── main.py            # 应用入口
│   ├── flask_app/         # Flask 应用
│   │   ├── __init__.py
│   │   ├── routes.py      # 主要路由
│   │   └── blueprints/    # 蓝图
│   ├── fastapi_app/       # FastAPI 应用
│   │   ├── __init__.py
│   │   ├── models.py      # Pydantic 模型
│   │   └── routers/       # API 路由器
│   └── common/            # 共享组件
│       ├── middleware.py  # 中间件
│       └── exceptions.py  # 异常处理
├── templates/             # Jinja2 模板
├── static/               # 静态文件
├── tests/                # 测试文件
└── utils/                # 工具类
    ├── log_util.py       # 日志工具
    └── constants.py      # 常量定义
```

## 功能特性

- **混合架构**: Flask 处理 Web 页面，FastAPI 处理 API 请求
- **BLE 模拟**: 设备扫描、连接、断开等操作的模拟
- **自动文档**: FastAPI 自动生成 API 文档
- **统一日志**: 集成的日志管理系统
- **响应式UI**: 基于 Bootstrap 5 的现代化界面

## API 端点

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/v1/health` | 健康检查 |
| POST | `/api/v1/ble/scan` | 扫描 BLE 设备 |
| POST | `/api/v1/ble/connect` | 连接设备 |
| GET | `/api/v1/ble/devices` | 获取已连接设备 |
| DELETE | `/api/v1/ble/disconnect/{address}` | 断开设备连接 |

## 环境变量

- `FLASK_ENV`: 运行环境 (development/production)
- `HOST`: 服务器地址 (默认: 0.0.0.0)
- `PORT`: 服务器端口 (默认: 8000)
- `DEBUG`: 调试模式 (默认: True)
- `LOG_LEVEL`: 日志级别 (默认: INFO)