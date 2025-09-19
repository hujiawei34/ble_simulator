"""BLE Business Service Layer"""
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.python.utils.constants import PROJECT_ROOT
from src.python.utils.log_util import LogUtil
from .bluetooth.device_manager import BluetoothDeviceManager
from .bluetooth.exceptions import (
    BluetoothException,
    BluetoothAdapterNotFoundError,
    BluetoothScanError,
    BluetoothConnectionError,
    BluetoothPermissionError
)

logger = LogUtil.get_logger('ble_service')


class BLEService:
    """BLE业务服务层"""

    def __init__(self):
        self.device_manager = BluetoothDeviceManager()
        self._service_status = "initialized"
        logger.info("BLE服务初始化完成")

    async def scan_devices(self,
                          duration: int = 10,
                          filter_name: Optional[str] = None,
                          filter_services: List[str] = None) -> Dict[str, Any]:
        """
        扫描BLE设备

        Args:
            duration: 扫描持续时间(秒)
            filter_name: 设备名称过滤
            filter_services: 服务UUID过滤

        Returns:
            扫描结果响应
        """
        logger.info(f"BLE服务开始扫描设备，参数: duration={duration}, filter_name={filter_name}")

        try:
            self._service_status = "scanning"

            devices = await self.device_manager.scan_and_cache_devices(
                duration=duration,
                filter_name=filter_name,
                filter_services=filter_services or []
            )

            # 转换设备信息格式以匹配API模型
            formatted_devices = []
            for device in devices:
                formatted_device = {
                    "name": device.get('name', 'Unknown Device'),
                    "address": device['address'],
                    "rssi": device.get('rssi'),
                    "services": device.get('services', []),
                    "manufacturer_data": device.get('manufacturer_data', {})
                }
                formatted_devices.append(formatted_device)

            response = {
                "status": "completed",
                "devices": formatted_devices,
                "scan_time": datetime.now(),
                "duration": duration,
                "total_found": len(formatted_devices)
            }

            self._service_status = "idle"
            logger.info(f"BLE扫描完成，发现 {len(formatted_devices)} 个设备")
            return response

        except BluetoothAdapterNotFoundError as e:
            logger.error(f"蓝牙适配器未找到: {str(e)}")
            self._service_status = "error"
            return {
                "status": "error",
                "error_type": "adapter_not_found",
                "error_message": str(e),
                "devices": [],
                "scan_time": datetime.now(),
                "duration": 0,
                "total_found": 0
            }

        except BluetoothPermissionError as e:
            logger.error(f"蓝牙权限不足: {str(e)}")
            self._service_status = "error"
            return {
                "status": "error",
                "error_type": "permission_denied",
                "error_message": str(e),
                "devices": [],
                "scan_time": datetime.now(),
                "duration": 0,
                "total_found": 0
            }

        except BluetoothScanError as e:
            logger.error(f"蓝牙扫描失败: {str(e)}")
            self._service_status = "error"
            return {
                "status": "error",
                "error_type": "scan_failed",
                "error_message": str(e),
                "devices": [],
                "scan_time": datetime.now(),
                "duration": 0,
                "total_found": 0
            }

        except Exception as e:
            logger.error(f"扫描过程中发生未知错误: {str(e)}")
            self._service_status = "error"
            return {
                "status": "error",
                "error_type": "unknown_error",
                "error_message": f"扫描失败: {str(e)}",
                "devices": [],
                "scan_time": datetime.now(),
                "duration": 0,
                "total_found": 0
            }

    async def connect_device(self,
                           device_address: str,
                           timeout: int = 30) -> Dict[str, Any]:
        """
        连接BLE设备

        Args:
            device_address: 设备MAC地址
            timeout: 连接超时时间

        Returns:
            连接结果响应
        """
        logger.info(f"BLE服务尝试连接设备: {device_address}")

        try:
            connection_info = await self.device_manager.connect_to_device(
                device_address, timeout
            )

            response = {
                "status": "connected",
                "device_address": device_address,
                "connected": True,
                "connection_time": connection_info['connection_time'],
                "services": connection_info.get('services', [])
            }

            logger.info(f"设备连接成功: {device_address}")
            return response

        except BluetoothConnectionError as e:
            logger.error(f"连接失败: {str(e)}")
            return {
                "status": "failed",
                "device_address": device_address,
                "connected": False,
                "error_message": str(e),
                "connection_time": None,
                "services": []
            }

        except Exception as e:
            logger.error(f"连接过程中发生未知错误: {str(e)}")
            return {
                "status": "error",
                "device_address": device_address,
                "connected": False,
                "error_message": f"连接失败: {str(e)}",
                "connection_time": None,
                "services": []
            }

    async def disconnect_device(self, device_address: str) -> Dict[str, Any]:
        """
        断开设备连接

        Args:
            device_address: 设备MAC地址

        Returns:
            断开连接结果响应
        """
        logger.info(f"BLE服务断开设备连接: {device_address}")

        try:
            success = await self.device_manager.disconnect_from_device(device_address)

            if success:
                logger.info(f"设备断开成功: {device_address}")
                return {
                    "success": True,
                    "message": f"已断开设备 {device_address} 的连接",
                    "device_address": device_address
                }
            else:
                logger.warning(f"设备断开失败: {device_address}")
                return {
                    "success": False,
                    "message": f"断开设备 {device_address} 连接失败",
                    "device_address": device_address
                }

        except Exception as e:
            logger.error(f"断开连接过程中发生错误: {str(e)}")
            return {
                "success": False,
                "message": f"断开连接失败: {str(e)}",
                "device_address": device_address
            }

    def get_connected_devices(self) -> List[Dict[str, Any]]:
        """
        获取已连接的设备列表

        Returns:
            已连接设备列表
        """
        logger.debug("获取已连接设备列表")

        try:
            connected_devices = self.device_manager.get_connected_devices()

            # 格式化设备信息以匹配API模型
            formatted_devices = []
            for device in connected_devices:
                formatted_device = {
                    "name": device.get('name', 'Unknown Device'),
                    "address": device['device_address'],
                    "rssi": device.get('rssi'),
                    "services": device.get('services', []),
                    "manufacturer_data": device.get('manufacturer_data', {}),
                    "connection_time": device.get('connection_time'),
                    "connected": True
                }
                formatted_devices.append(formatted_device)

            logger.debug(f"返回已连接设备 {len(formatted_devices)} 个")
            return formatted_devices

        except Exception as e:
            logger.error(f"获取已连接设备列表失败: {str(e)}")
            return []

    def get_cached_devices(self) -> List[Dict[str, Any]]:
        """
        获取缓存的设备列表

        Returns:
            缓存的设备列表
        """
        logger.debug("获取缓存设备列表")

        try:
            cached_devices = self.device_manager.get_cached_devices()

            # 格式化设备信息
            formatted_devices = []
            for device in cached_devices:
                formatted_device = {
                    "name": device.get('name', 'Unknown Device'),
                    "address": device['address'],
                    "rssi": device.get('rssi'),
                    "services": device.get('services', []),
                    "manufacturer_data": device.get('manufacturer_data', {}),
                    "last_seen": device.get('last_seen'),
                    "connected": self.device_manager.is_device_connected(device['address'])
                }
                formatted_devices.append(formatted_device)

            logger.debug(f"返回缓存设备 {len(formatted_devices)} 个")
            return formatted_devices

        except Exception as e:
            logger.error(f"获取缓存设备列表失败: {str(e)}")
            return []

    def get_service_status(self) -> Dict[str, Any]:
        """
        获取服务状态信息

        Returns:
            服务状态信息
        """
        try:
            stats = self.device_manager.get_statistics()
            return {
                "service_status": self._service_status,
                "statistics": stats,
                "timestamp": datetime.now()
            }
        except Exception as e:
            logger.error(f"获取服务状态失败: {str(e)}")
            return {
                "service_status": "error",
                "error_message": str(e),
                "timestamp": datetime.now()
            }

    async def refresh_device_cache(self) -> Dict[str, Any]:
        """刷新设备缓存"""
        logger.info("刷新设备缓存")
        try:
            await self.device_manager.refresh_device_cache()
            return {
                "success": True,
                "message": "设备缓存已刷新"
            }
        except Exception as e:
            logger.error(f"刷新设备缓存失败: {str(e)}")
            return {
                "success": False,
                "message": f"刷新缓存失败: {str(e)}"
            }

    async def shutdown(self):
        """关闭BLE服务"""
        logger.info("关闭BLE服务")
        try:
            await self.device_manager.shutdown()
            self._service_status = "shutdown"
            logger.info("BLE服务已关闭")
        except Exception as e:
            logger.error(f"关闭BLE服务失败: {str(e)}")


# 全局BLE服务实例
ble_service = BLEService()