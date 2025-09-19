"""BLE API Router"""
from fastapi import APIRouter, HTTPException, status
from typing import List
from datetime import datetime

from src.python.utils.log_util import LogUtil
from src.python.service.ble_service import ble_service
from ..models import (
    DeviceInfo, ScanRequest, ScanResponse,
    ConnectionRequest, ConnectionResponse,
    ApiResponse, HealthResponse
)

router = APIRouter(prefix="/ble", tags=["BLE Operations"])
logger = LogUtil.get_logger('ble_api')

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """API健康检查"""
    logger.info("API健康检查")
    return HealthResponse()

@router.post("/scan", response_model=ScanResponse)
async def scan_devices(scan_request: ScanRequest):
    """扫描BLE设备"""
    logger.info(f"开始扫描BLE设备，持续时间: {scan_request.duration}秒")

    try:
        # 调用真实蓝牙扫描服务
        scan_result = await ble_service.scan_devices(
            duration=scan_request.duration,
            filter_name=scan_request.filter_name,
            filter_services=scan_request.filter_services
        )

        # 如果扫描出错，返回错误但不抛出异常
        if scan_result["status"] == "error":
            logger.warning(f"BLE扫描出错: {scan_result.get('error_message')}")
            # 可以选择返回空设备列表或抛出异常
            devices = []
            status = "completed_with_errors"
        else:
            devices = [DeviceInfo(**device) for device in scan_result["devices"]]
            status = scan_result["status"]

        logger.info(f"扫描完成，发现 {len(devices)} 个设备")

        return ScanResponse(
            status=status,
            devices=devices,
            duration=scan_request.duration,
            scan_time=scan_result.get("scan_time", datetime.now())
        )

    except Exception as e:
        logger.error(f"扫描过程中发生异常: {str(e)}")
        # 如果真实扫描失败，可以选择返回模拟数据或抛出异常
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"扫描设备失败: {str(e)}"
        )

@router.post("/connect", response_model=ConnectionResponse)
async def connect_device(connection_request: ConnectionRequest):
    """连接到BLE设备"""
    logger.info(f"尝试连接到设备: {connection_request.device_address}")

    try:
        # 调用真实蓝牙连接服务
        connection_result = await ble_service.connect_device(
            device_address=connection_request.device_address,
            timeout=connection_request.timeout
        )

        if connection_result["connected"]:
            return ConnectionResponse(
                status=connection_result["status"],
                device_address=connection_result["device_address"],
                connected=connection_result["connected"],
                connection_time=connection_result["connection_time"],
                services=connection_result["services"]
            )
        else:
            logger.warning(f"连接失败: {connection_request.device_address}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=connection_result.get("error_message", "设备未找到或连接失败")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"连接过程中发生异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"连接设备失败: {str(e)}"
        )

@router.delete("/disconnect/{device_address}")
async def disconnect_device(device_address: str):
    """断开设备连接"""
    logger.info(f"断开设备连接: {device_address}")

    try:
        # 调用真实蓝牙断开连接服务
        disconnect_result = await ble_service.disconnect_device(device_address)

        return ApiResponse(
            success=disconnect_result["success"],
            message=disconnect_result["message"]
        )

    except Exception as e:
        logger.error(f"断开连接过程中发生异常: {str(e)}")
        return ApiResponse(
            success=False,
            message=f"断开连接失败: {str(e)}"
        )

@router.get("/devices", response_model=List[DeviceInfo])
async def get_connected_devices():
    """获取已连接的设备列表"""
    logger.info("获取已连接设备列表")

    try:
        # 调用真实蓝牙服务获取已连接设备
        connected_devices_data = ble_service.get_connected_devices()

        connected_devices = [DeviceInfo(**device) for device in connected_devices_data]

        logger.info(f"返回已连接设备: {len(connected_devices)} 个")
        return connected_devices

    except Exception as e:
        logger.error(f"获取已连接设备列表失败: {str(e)}")
        return []