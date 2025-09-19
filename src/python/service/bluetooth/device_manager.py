"""Bluetooth Device Manager"""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.python.utils.constants import PROJECT_ROOT
from src.python.utils.log_util import LogUtil
from .scanner import BluetoothScanner
from .connector import BluetoothConnector
from .exceptions import (
    BluetoothException,
    DeviceNotFoundError
)

logger = LogUtil.get_logger('bluetooth_device_manager')


class BluetoothDeviceManager:
    """蓝牙设备管理器"""

    def __init__(self):
        self.scanner = BluetoothScanner()
        self.connector = BluetoothConnector()
        self._device_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timeout = timedelta(minutes=5)  # 设备缓存5分钟过期

    async def scan_and_cache_devices(self,
                                   duration: int = 10,
                                   filter_name: Optional[str] = None,
                                   filter_services: List[str] = None) -> List[Dict[str, Any]]:
        """
        扫描并缓存设备

        Args:
            duration: 扫描持续时间
            filter_name: 设备名称过滤
            filter_services: 服务UUID过滤

        Returns:
            发现的设备列表
        """
        logger.info("开始扫描并缓存设备")

        try:
            devices = await self.scanner.scan_devices(
                duration=duration,
                filter_name=filter_name,
                filter_services=filter_services
            )

            # 更新设备缓存
            current_time = datetime.now()
            for device in devices:
                address = device['address']
                device['last_seen'] = current_time
                device['scan_time'] = current_time
                self._device_cache[address] = device

            logger.info(f"设备扫描完成，缓存了 {len(devices)} 个设备")
            return devices

        except BluetoothException as e:
            logger.error(f"设备扫描失败: {str(e)}")
            raise

    def get_cached_devices(self, include_expired: bool = False) -> List[Dict[str, Any]]:
        """
        获取缓存的设备列表

        Args:
            include_expired: 是否包含过期的设备

        Returns:
            缓存的设备列表
        """
        if not include_expired:
            self._cleanup_expired_devices()

        devices = list(self._device_cache.values())
        logger.debug(f"返回缓存设备 {len(devices)} 个")
        return devices

    def get_device_by_address(self, device_address: str) -> Optional[Dict[str, Any]]:
        """
        根据地址获取设备信息

        Args:
            device_address: 设备MAC地址

        Returns:
            设备信息或None
        """
        device = self._device_cache.get(device_address)
        if device and not self._is_device_expired(device):
            return device.copy()
        return None

    async def connect_to_device(self,
                              device_address: str,
                              timeout: int = 30) -> Dict[str, Any]:
        """
        连接到设备

        Args:
            device_address: 设备MAC地址
            timeout: 连接超时时间

        Returns:
            连接信息
        """
        logger.info(f"尝试连接设备: {device_address}")

        # 检查设备是否在缓存中
        device = self.get_device_by_address(device_address)
        if not device:
            logger.warning(f"设备不在缓存中，尝试连接: {device_address}")

        try:
            connection_info = await self.connector.connect_device(
                device_address, timeout
            )

            # 更新设备缓存中的连接状态
            if device_address in self._device_cache:
                self._device_cache[device_address].update({
                    'connected': True,
                    'connection_time': connection_info['connection_time'],
                    'services': connection_info['services']
                })

            return connection_info

        except BluetoothException as e:
            logger.error(f"连接设备失败: {str(e)}")
            raise

    async def disconnect_from_device(self, device_address: str) -> bool:
        """
        断开设备连接

        Args:
            device_address: 设备MAC地址

        Returns:
            是否成功断开
        """
        logger.info(f"断开设备连接: {device_address}")

        try:
            success = await self.connector.disconnect_device(device_address)

            # 更新设备缓存中的连接状态
            if device_address in self._device_cache:
                self._device_cache[device_address].update({
                    'connected': False,
                    'connection_time': None
                })

            return success

        except BluetoothException as e:
            logger.error(f"断开设备连接失败: {str(e)}")
            raise

    def get_connected_devices(self) -> List[Dict[str, Any]]:
        """获取所有已连接的设备"""
        connected_devices = self.connector.get_connected_devices()

        # 合并缓存信息和连接信息
        for conn_device in connected_devices:
            address = conn_device['device_address']
            cached_device = self._device_cache.get(address, {})

            # 合并设备信息
            conn_device.update({
                'name': cached_device.get('name', 'Unknown Device'),
                'rssi': cached_device.get('rssi'),
                'manufacturer_data': cached_device.get('manufacturer_data', {})
            })

        return connected_devices

    def get_device_connection_info(self, device_address: str) -> Optional[Dict[str, Any]]:
        """获取设备连接信息"""
        return self.connector.get_connection_info(device_address)

    async def get_device_client(self, device_address: str):
        """获取设备的BleakClient实例"""
        return await self.connector.get_device_client(device_address)

    def is_device_connected(self, device_address: str) -> bool:
        """检查设备是否已连接"""
        return self.connector.is_connected(device_address)

    def _cleanup_expired_devices(self):
        """清理过期的设备缓存"""
        current_time = datetime.now()
        expired_addresses = []

        for address, device in self._device_cache.items():
            if self._is_device_expired(device, current_time):
                expired_addresses.append(address)

        for address in expired_addresses:
            del self._device_cache[address]

        if expired_addresses:
            logger.debug(f"清理过期设备缓存: {len(expired_addresses)} 个")

    def _is_device_expired(self,
                          device: Dict[str, Any],
                          current_time: Optional[datetime] = None) -> bool:
        """检查设备缓存是否过期"""
        if current_time is None:
            current_time = datetime.now()

        last_seen = device.get('last_seen')
        if not last_seen:
            return True

        return (current_time - last_seen) > self._cache_timeout

    async def refresh_device_cache(self):
        """刷新设备缓存（重新扫描）"""
        logger.info("刷新设备缓存")
        await self.scan_and_cache_devices()

    def clear_device_cache(self):
        """清空设备缓存"""
        logger.info("清空设备缓存")
        self._device_cache.clear()

    async def shutdown(self):
        """关闭设备管理器，断开所有连接"""
        logger.info("关闭设备管理器")
        await self.connector.disconnect_all()
        await self.scanner.stop_scan()
        self.clear_device_cache()

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        connected_count = len(self.connector.get_connected_devices())
        cached_count = len(self._device_cache)

        return {
            'cached_devices': cached_count,
            'connected_devices': connected_count,
            'is_scanning': self.scanner.is_scanning(),
            'cache_timeout_minutes': self._cache_timeout.total_seconds() / 60
        }