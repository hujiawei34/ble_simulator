"""BLE API Router"""
from fastapi import APIRouter, HTTPException, status
from typing import List
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.python.utils.log_util import LogUtil
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

    # 模拟扫描设备
    mock_devices = [
        DeviceInfo(
            name="iPhone 12",
            address="AA:BB:CC:DD:EE:FF",
            rssi=-45,
            services=["180F", "180A"],
            manufacturer_data={"0x004C": "Apple Inc."}
        ),
        DeviceInfo(
            name="Fitbit Versa",
            address="11:22:33:44:55:66",
            rssi=-62,
            services=["180F", "1812"],
            manufacturer_data={"0x0057": "Fitbit Inc."}
        )
    ]

    if scan_request.filter_name:
        mock_devices = [
            device for device in mock_devices
            if device.name and scan_request.filter_name.lower() in device.name.lower()
        ]

    logger.info(f"扫描完成，发现 {len(mock_devices)} 个设备")

    return ScanResponse(
        status="completed",
        devices=mock_devices,
        duration=scan_request.duration
    )

@router.post("/connect", response_model=ConnectionResponse)
async def connect_device(connection_request: ConnectionRequest):
    """连接到BLE设备"""
    logger.info(f"尝试连接到设备: {connection_request.device_address}")

    # 模拟连接过程
    if connection_request.device_address == "AA:BB:CC:DD:EE:FF":
        return ConnectionResponse(
            status="connected",
            device_address=connection_request.device_address,
            connected=True,
            connection_time=datetime.now(),
            services=["180F", "180A", "1800", "1801"]
        )
    else:
        logger.warning(f"连接失败: {connection_request.device_address}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="设备未找到或连接失败"
        )

@router.delete("/disconnect/{device_address}")
async def disconnect_device(device_address: str):
    """断开设备连接"""
    logger.info(f"断开设备连接: {device_address}")

    return ApiResponse(
        success=True,
        message=f"已断开设备 {device_address} 的连接"
    )

@router.get("/devices", response_model=List[DeviceInfo])
async def get_connected_devices():
    """获取已连接的设备列表"""
    logger.info("获取已连接设备列表")

    # 模拟已连接设备
    connected_devices = [
        DeviceInfo(
            name="iPhone 12",
            address="AA:BB:CC:DD:EE:FF",
            rssi=-45,
            services=["180F", "180A"]
        )
    ]

    return connected_devices