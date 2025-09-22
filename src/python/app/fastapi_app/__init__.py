"""FastAPI Application Module"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.python.utils.log_util import LogUtil
from .routers import ble_api, general, peripheral_api

logger = LogUtil.get_logger('fastapi_app')

def create_fastapi_app(config) -> FastAPI:
    """FastAPI应用工厂函数"""
    logger.info("创建FastAPI应用实例")

    app = FastAPI(
        title=config.PROJECT_NAME,
        version=config.PROJECT_VERSION,
        description="BLE Simulator FastAPI Service",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # 添加CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 在生产环境中应该限制来源
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由器
    app.include_router(general.router, prefix=config.API_V1_STR)
    app.include_router(ble_api.router, prefix=config.API_V1_STR)
    app.include_router(peripheral_api.router, prefix=config.API_V1_STR)

    logger.info("FastAPI应用创建完成")
    logger.info(f"API文档地址: /docs")
    logger.info(f"API前缀: {config.API_V1_STR}")

    return app