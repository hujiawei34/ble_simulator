"""Main Application Entry Point"""
import sys
import signal
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.python.utils.log_util import LogUtil
from .config import get_config
from .flask_app import create_flask_app
from .fastapi_app import create_fastapi_app
from .common.middleware import setup_flask_middleware
from .common.exceptions import setup_flask_error_handlers

from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
import uvicorn

logger = LogUtil.get_logger('main_app')

def signal_handler(signum, frame):
    """处理系统信号的函数"""
    signal_name = {
        signal.SIGTERM: "SIGTERM",
        signal.SIGINT: "SIGINT"
    }.get(signum, f"SIGNAL({signum})")

    logger.info(f"收到信号 {signal_name}，正在优雅关闭服务...")
    sys.exit(0)

def create_app():
    """创建混合应用"""
    logger.info("开始创建混合应用")

    # 获取配置
    config = get_config()
    logger.info(f"使用配置: {config.__class__.__name__}")

    # 创建FastAPI应用作为主应用
    fastapi_app = create_fastapi_app(config)

    # 创建Flask应用
    flask_app = create_flask_app(config)
    setup_flask_middleware(flask_app)
    setup_flask_error_handlers(flask_app)

    # 将Flask应用作为WSGI中间件挂载到FastAPI
    # FastAPI处理所有 /api 路径的请求
    # Flask处理所有其他路径的请求
    fastapi_app.mount("/", WSGIMiddleware(flask_app))

    logger.info("混合应用创建完成")
    logger.info("FastAPI应用处理: /api (所有API请求)")
    logger.info("Flask应用处理: / (所有Web页面)")
    logger.info(f"API文档地址: /docs")

    return fastapi_app, config

# 全局应用实例
app, app_config = create_app()

def run_server():
    """运行服务器"""
    # 注册信号处理器
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    logger.info("已注册信号处理器 (SIGTERM, SIGINT)")

    logger.info(f"启动服务器 http://{app_config.HOST}:{app_config.PORT}")
    logger.info(f"Web界面: http://localhost:{app_config.PORT}/")
    logger.info(f"API文档: http://localhost:{app_config.PORT}/docs")

    # 使用uvicorn运行混合应用
    uvicorn.run(
        "src.python.app.main:app",
        host=app_config.HOST,
        port=app_config.PORT,
        reload=app_config.DEBUG,
        log_level=app_config.LOG_LEVEL.lower()
    )

if __name__ == "__main__":
    run_server()