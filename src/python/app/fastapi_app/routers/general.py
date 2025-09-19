"""General API Router"""
from fastapi import APIRouter
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.python.utils.log_util import LogUtil
from ..models import HealthResponse, ApiResponse

router = APIRouter(tags=["General"])
logger = LogUtil.get_logger('general_api')

@router.get("/", response_model=ApiResponse)
async def root():
    """API根路径"""
    logger.info("访问API根路径")
    return ApiResponse(
        success=True,
        message="BLE Simulator FastAPI Service",
        data={
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health"
        }
    )

@router.get("/health", response_model=HealthResponse)
async def health():
    """通用健康检查"""
    logger.info("通用健康检查")
    return HealthResponse()

@router.get("/version")
async def version():
    """获取API版本信息"""
    logger.info("获取版本信息")
    return {
        "service": "BLE Simulator",
        "api_version": "1.0.0",
        "framework": "FastAPI"
    }