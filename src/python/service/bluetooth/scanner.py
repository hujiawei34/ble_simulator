"""Bluetooth Scanner Implementation"""
import asyncio
from typing import List, Dict, Any, Optional
from bleak import BleakScanner, BleakError
import sys

from src.python.utils.constants import PROJECT_ROOT
from src.python.utils.log_util import LogUtil
from .exceptions import (
    BluetoothScanError,
    BluetoothAdapterNotFoundError,
    BluetoothPermissionError
)

logger = LogUtil.get_logger('bluetooth_scanner')


class BluetoothScanner:
    """蓝牙设备扫描器"""

    def __init__(self):
        self._is_scanning = False
        self._discovered_devices = {}

    async def scan_devices(self,
                          duration: int = 10,
                          filter_name: Optional[str] = None,
                          filter_services: List[str] = None) -> List[Dict[str, Any]]:
        """
        扫描BLE设备

        Args:
            duration: 扫描持续时间(秒)
            filter_name: 设备名称过滤
            filter_services: 服务UUID过滤

        Returns:
            发现的设备列表

        Raises:
            BluetoothScanError: 扫描失败
            BluetoothAdapterNotFoundError: 适配器未找到
            BluetoothPermissionError: 权限不足
        """
        logger.info(f"开始扫描BLE设备，持续时间: {duration}秒")

        try:
            self._is_scanning = True
            self._discovered_devices = {}

            # 执行扫描，添加额外的超时保护
            logger.info("正在初始化BLE扫描器...")
            devices = await asyncio.wait_for(
                BleakScanner.discover(timeout=duration),
                timeout=duration + 5  # 比bleak超时多5秒
            )
            logger.info(f"扫描器返回了 {len(devices)} 个设备")

            discovered_devices = []
            logger.info("开始处理发现的设备...")
            for i, device in enumerate(devices, 1):
                logger.info(f"处理设备 {i}/{len(devices)}: {device.name or 'Unknown'} ({device.address}) RSSI: {getattr(device, 'rssi', 'N/A')}")

                device_info = await self._extract_device_info(device)

                # 应用过滤器
                if self._should_include_device(device_info, filter_name, filter_services):
                    discovered_devices.append(device_info)
                    self._discovered_devices[device.address] = device_info
                    logger.info(f"设备已添加到结果: {device_info['name']} ({device_info['address']})")
                else:
                    logger.debug(f"设备被过滤器排除: {device_info['name']} ({device_info['address']})")

            logger.info(f"扫描完成，发现 {len(discovered_devices)} 个设备")
            return discovered_devices

        except asyncio.TimeoutError:
            error_msg = f"BLE扫描超时 ({duration + 5}秒)"
            logger.error(error_msg)
            raise BluetoothScanError(error_msg)

        except BleakError as e:
            error_msg = f"BLE扫描失败: {str(e)}"
            logger.error(error_msg)

            # 根据错误类型抛出相应异常
            if "adapter" in str(e).lower():
                raise BluetoothAdapterNotFoundError(f"蓝牙适配器问题: {str(e)}")
            elif "permission" in str(e).lower():
                raise BluetoothPermissionError(f"权限不足: {str(e)}")
            else:
                raise BluetoothScanError(error_msg)

        except Exception as e:
            error_msg = f"未知扫描错误: {str(e)}"
            logger.error(error_msg)
            raise BluetoothScanError(error_msg)

        finally:
            self._is_scanning = False

    async def _extract_device_info(self, device) -> Dict[str, Any]:
        """提取设备信息"""
        # 获取服务UUID列表
        services = []
        if hasattr(device, 'metadata') and 'uuids' in device.metadata:
            services = list(device.metadata.get('uuids', []))

        # 获取制造商数据
        manufacturer_data = {}
        if hasattr(device, 'metadata') and 'manufacturer_data' in device.metadata:
            raw_data = device.metadata.get('manufacturer_data', {})
            # 转换为字符串键值对
            for key, value in raw_data.items():
                manufacturer_data[f"0x{key:04X}"] = value.hex() if isinstance(value, bytes) else str(value)

        return {
            "name": device.name or "Unknown Device",
            "address": device.address,
            "rssi": getattr(device, 'rssi', None),
            "services": services,
            "manufacturer_data": manufacturer_data
        }

    def _should_include_device(self,
                              device_info: Dict[str, Any],
                              filter_name: Optional[str],
                              filter_services: List[str]) -> bool:
        """判断设备是否符合过滤条件"""
        # 名称过滤
        if filter_name:
            device_name = device_info.get('name', '').lower()
            if filter_name.lower() not in device_name:
                return False

        # 服务过滤
        if filter_services:
            device_services = [s.lower() for s in device_info.get('services', [])]
            for service in filter_services:
                if service.lower() not in device_services:
                    return False

        return True

    def get_cached_devices(self) -> Dict[str, Dict[str, Any]]:
        """获取缓存的设备列表"""
        return self._discovered_devices.copy()

    def is_scanning(self) -> bool:
        """检查是否正在扫描"""
        return self._is_scanning

    async def stop_scan(self):
        """停止扫描"""
        if self._is_scanning:
            logger.info("停止BLE扫描")
            self._is_scanning = False