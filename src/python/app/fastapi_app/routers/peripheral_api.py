"""BLE Peripheral API Router"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from src.python.utils.log_util import LogUtil
from src.python.service.ble_peripheral_service import ble_peripheral_service

router = APIRouter(prefix="/peripheral", tags=["BLE Peripheral"])
logger = LogUtil.get_logger('peripheral_api')


class PeripheralStartRequest(BaseModel):
    """外围设备启动请求"""
    adapter_path: Optional[str] = '/org/bluez/hci0'


class PeripheralResponse(BaseModel):
    """外围设备响应"""
    success: bool
    message: str
    data: Optional[dict] = None


class GripDataRequest(BaseModel):
    """握力数据请求"""
    data: str


class SimulationModeRequest(BaseModel):
    """模拟模式请求"""
    mode: str  # normal, exercise, rest


class PeripheralStatus(BaseModel):
    """外围设备状态"""
    is_initialized: bool
    is_running: bool
    connected_clients: int
    data_sent_count: int
    start_time: Optional[str] = None
    running_duration_seconds: Optional[float] = None
    advertisement: dict
    gatt_server: dict
    grip_simulator: dict


class HistoryDataItem(BaseModel):
    """历史数据项"""
    data: str
    timestamp: str


@router.post("/initialize", response_model=PeripheralResponse)
async def initialize_peripheral(request: PeripheralStartRequest):
    """初始化BLE外围设备服务"""
    logger.info(f"初始化BLE外围设备服务，适配器: {request.adapter_path}")

    try:
        if ble_peripheral_service.is_initialized:
            return PeripheralResponse(
                success=False,
                message="BLE外围设备服务已初始化"
            )

        success = ble_peripheral_service.initialize(request.adapter_path)

        if success:
            return PeripheralResponse(
                success=True,
                message="BLE外围设备服务初始化成功",
                data={"adapter_path": request.adapter_path}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="BLE外围设备服务初始化失败"
            )

    except Exception as e:
        logger.error(f"初始化BLE外围设备服务失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"初始化失败: {str(e)}"
        )


@router.post("/start", response_model=PeripheralResponse)
async def start_peripheral():
    """启动BLE外围设备模式"""
    logger.info("启动BLE外围设备模式")

    try:
        # start_peripheral 方法会自动检查并初始化服务
        result = ble_peripheral_service.start_peripheral()

        if result["success"]:
            return PeripheralResponse(
                success=True,
                message=result["message"],
                data={
                    "start_time": result.get("start_time"),
                    "device_name": result.get("device_name")
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动BLE外围设备模式失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动失败: {str(e)}"
        )


@router.post("/stop", response_model=PeripheralResponse)
async def stop_peripheral():
    """停止BLE外围设备模式"""
    logger.info("停止BLE外围设备模式")

    try:
        result = ble_peripheral_service.stop_peripheral()

        if result["success"]:
            return PeripheralResponse(
                success=True,
                message=result["message"],
                data={
                    "stop_time": result.get("stop_time"),
                    "duration_seconds": result.get("duration_seconds"),
                    "data_sent_count": result.get("data_sent_count")
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停止BLE外围设备模式失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"停止失败: {str(e)}"
        )


@router.get("/status", response_model=PeripheralStatus)
async def get_peripheral_status():
    """获取BLE外围设备状态"""
    logger.debug("获取BLE外围设备状态")

    try:
        status_data = ble_peripheral_service.get_status()
        return PeripheralStatus(**status_data)

    except Exception as e:
        logger.error(f"获取外围设备状态失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取状态失败: {str(e)}"
        )


@router.get("/data/current")
async def get_current_grip_data():
    """获取当前握力数据"""
    logger.debug("获取当前握力数据")

    try:
        current_data = ble_peripheral_service.get_current_grip_data()
        return {
            "data": current_data,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"获取当前握力数据失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取数据失败: {str(e)}"
        )


@router.post("/data/set", response_model=PeripheralResponse)
async def set_grip_data(request: GripDataRequest):
    """设置握力数据"""
    logger.info(f"设置握力数据: {request.data}")

    try:
        result = ble_peripheral_service.set_grip_data(request.data)

        if result["success"]:
            return PeripheralResponse(
                success=True,
                message=result["message"],
                data={"data": result["data"]}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"设置握力数据失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"设置数据失败: {str(e)}"
        )


@router.post("/simulation/mode", response_model=PeripheralResponse)
async def set_simulation_mode(request: SimulationModeRequest):
    """设置模拟模式"""
    logger.info(f"设置模拟模式: {request.mode}")

    if request.mode not in ["normal", "exercise", "rest"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的模拟模式，支持的模式: normal, exercise, rest"
        )

    try:
        result = ble_peripheral_service.set_simulation_mode(request.mode)

        if result["success"]:
            return PeripheralResponse(
                success=True,
                message=result["message"],
                data={"mode": result["mode"]}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"设置模拟模式失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"设置模式失败: {str(e)}"
        )


@router.get("/data/history", response_model=List[HistoryDataItem])
async def get_data_history(limit: int = 100):
    """获取历史数据"""
    logger.debug(f"获取历史数据，限制: {limit}")

    if limit <= 0 or limit > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="限制参数必须在1-1000之间"
        )

    try:
        history = ble_peripheral_service.get_data_history(limit)
        return [HistoryDataItem(**item) for item in history]

    except Exception as e:
        logger.error(f"获取历史数据失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取历史数据失败: {str(e)}"
        )


@router.get("/health")
async def peripheral_health_check():
    """外围设备健康检查"""
    logger.debug("外围设备健康检查")

    try:
        status = ble_peripheral_service.get_status()
        return {
            "service": "BLE Peripheral",
            "status": "healthy",
            "is_initialized": status["is_initialized"],
            "is_running": status["is_running"],
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return {
            "service": "BLE Peripheral",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }