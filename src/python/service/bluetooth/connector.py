"""Bluetooth Connection Implementation"""
import asyncio
from typing import Dict, Any, List, Optional
from bleak import BleakClient, BleakError
from datetime import datetime

from src.python.utils.constants import PROJECT_ROOT
from src.python.utils.log_util import LogUtil
from .exceptions import (
    BluetoothConnectionError,
    DeviceNotFoundError,
    DeviceAlreadyConnectedError
)

logger = LogUtil.get_logger('bluetooth_connector')


class BluetoothConnector:
    """蓝牙设备连接器"""

    def __init__(self):
        self._connected_clients: Dict[str, BleakClient] = {}
        self._connection_info: Dict[str, Dict[str, Any]] = {}

    def _pairing_handler(self, sender, data):
        """配对处理回调函数 - 自动接受配对"""
        logger.info(f"=== 蓝牙配对请求 ===")
        logger.info(f"发送方: {sender}")
        logger.info(f"配对数据: {data}")
        logger.info(f"数据类型: {type(data)}")

        # 记录配对码（如果存在）
        if hasattr(data, 'passkey'):
            logger.info(f"🔑 配对码: {data.passkey}")
        elif hasattr(data, 'pin'):
            logger.info(f"🔑 PIN码: {data.pin}")
        elif isinstance(data, (int, str)):
            logger.info(f"🔑 配对码: {data}")

        logger.info("✅ 自动接受配对请求")
        logger.info("===================")

        # 自动接受配对
        return True

    def _disconnect_callback(self, client):
        """设备断开连接回调"""
        logger.info(f"设备断开连接: {client.address}")
        # 清理连接状态
        self._cleanup_disconnected_device(client.address)

    async def connect_device(self,
                           device_address: str,
                           timeout: int = 30) -> Dict[str, Any]:
        """
        连接BLE设备，支持配对

        Args:
            device_address: 设备MAC地址
            timeout: 连接超时时间(秒)

        Returns:
            连接信息字典

        Raises:
            BluetoothConnectionError: 连接失败
            DeviceAlreadyConnectedError: 设备已连接
        """
        logger.info(f"开始连接设备: {device_address}")
        logger.info(f"连接参数: timeout={timeout}秒")

        # 检查是否已连接
        if self.is_connected(device_address):
            logger.warning(f"设备已连接: {device_address}")
            raise DeviceAlreadyConnectedError(device_address)

        client = None
        try:
            logger.info(f"创建BleakClient实例: {device_address}")
            client = BleakClient(device_address, timeout=timeout)

            # 注意：bleak 1.1.1版本可能不支持set_disconnected_callback
            # 尝试设置断开连接回调（如果支持的话）
            if hasattr(client, 'set_disconnected_callback'):
                client.set_disconnected_callback(self._disconnect_callback)
            else:
                logger.debug("当前bleak版本不支持set_disconnected_callback")

            # 先尝试配对（会触发手机等设备的配对弹窗）
            logger.info("检查是否需要配对...")
            try:
                await self._attempt_pairing(client, device_address)
                logger.info("配对流程完成，开始建立连接...")
            except Exception as e:
                logger.info(f"配对跳过或失败: {str(e)}，直接尝试连接...")

            logger.info("尝试建立连接...")
            await asyncio.wait_for(
                client.connect(),
                timeout=timeout + 5
            )

            logger.info(f"检查连接状态: {client.is_connected}")
            if not client.is_connected:
                raise BluetoothConnectionError(device_address, "连接建立失败")

            logger.info("连接成功，获取设备服务...")
            # 获取设备服务
            services = await self._get_device_services(client)

            # 保存连接信息
            connection_info = {
                "device_address": device_address,
                "connected": True,
                "connection_time": datetime.now(),
                "services": services,
                "status": "connected"
            }

            self._connected_clients[device_address] = client
            self._connection_info[device_address] = connection_info

            logger.info(f"设备连接成功: {device_address}")
            return connection_info

        except asyncio.TimeoutError:
            error_msg = f"连接超时 ({timeout + 5}秒)"
            logger.error(f"连接设备 {device_address} 失败: {error_msg}")
            if client:
                try:
                    await client.disconnect()
                except Exception:
                    pass
            raise BluetoothConnectionError(device_address, error_msg)

        except BleakError as e:
            error_msg = f"BLE连接错误: {str(e)}"
            logger.error(f"连接设备 {device_address} 失败: {error_msg}")

            # 检查是否是配对相关错误
            if "pair" in str(e).lower() or "bond" in str(e).lower():
                logger.info("检测到配对相关错误，尝试配对...")
                try:
                    await self._attempt_pairing(client, device_address)
                    return await self.connect_device(device_address, timeout)
                except Exception as pair_error:
                    logger.error(f"配对失败: {str(pair_error)}")

            if client:
                try:
                    await client.disconnect()
                except Exception:
                    pass
            raise BluetoothConnectionError(device_address, error_msg)

        except Exception as e:
            error_msg = f"未知连接错误: {str(e)}"
            logger.error(f"连接设备 {device_address} 失败: {error_msg}")
            logger.error(f"错误类型: {type(e).__name__}")
            if client:
                try:
                    await client.disconnect()
                except Exception:
                    pass
            raise BluetoothConnectionError(device_address, error_msg)

    async def disconnect_device(self, device_address: str) -> bool:
        """
        断开设备连接

        Args:
            device_address: 设备MAC地址

        Returns:
            是否成功断开

        Raises:
            DeviceNotFoundError: 设备未连接
        """
        logger.info(f"断开设备连接: {device_address}")

        if not self.is_connected(device_address):
            raise DeviceNotFoundError(device_address, "设备未连接")

        try:
            client = self._connected_clients[device_address]
            await client.disconnect()

            # 清理连接信息
            del self._connected_clients[device_address]
            del self._connection_info[device_address]

            logger.info(f"设备断开成功: {device_address}")
            return True

        except Exception as e:
            logger.error(f"断开设备 {device_address} 失败: {str(e)}")
            # 即使断开失败也清理本地状态
            self._connected_clients.pop(device_address, None)
            self._connection_info.pop(device_address, None)
            return False

    async def _attempt_pairing(self, client: BleakClient, device_address: str):
        """尝试与设备配对"""
        logger.info(f"🔄 开始配对过程: {device_address}")

        # 检查设备是否已经配对
        try:
            if hasattr(client, 'is_paired'):
                is_paired = await client.is_paired()
                logger.info(f"设备配对状态: {is_paired}")
                if is_paired:
                    logger.info("✅ 设备已配对，跳过配对过程")
                    return
        except Exception as e:
            logger.debug(f"无法检查配对状态: {e}")

        try:
            # 设置配对处理回调（如果支持）
            pairing_callback_set = False
            if hasattr(client, 'set_pairing_handler'):
                client.set_pairing_handler(self._pairing_handler)
                logger.info("✅ 已设置配对处理回调")
                pairing_callback_set = True
            elif hasattr(client, 'pairing_handler'):
                client.pairing_handler = self._pairing_handler
                logger.info("✅ 已设置配对处理属性")
                pairing_callback_set = True
            else:
                logger.warning("⚠️  当前bleak版本不支持配对处理回调")

            logger.info(f"📱 发起配对请求到设备: {device_address}")
            logger.info("💭 此时手机上应该弹出配对请求窗口...")

            # 尝试配对
            await client.pair()
            logger.info(f"✅ 配对成功: {device_address}")

        except Exception as e:
            logger.error(f"❌ 配对失败: {str(e)}")
            logger.error(f"错误类型: {type(e).__name__}")

            # 检查是否是特定的配对错误
            error_str = str(e).lower()
            if 'already paired' in error_str:
                logger.info("✅ 设备已经配对过了")
                return
            elif 'not supported' in error_str:
                logger.info("ℹ️  设备不需要配对或不支持配对")
                return
            else:
                # 其他配对错误，继续尝试连接
                logger.info("⚠️  配对失败，但继续尝试连接...")
                raise

    async def _get_device_services(self, client: BleakClient) -> List[str]:
        """获取设备服务列表"""
        try:
            logger.info("正在获取设备服务列表...")
            services = []
            device_services = client.services

            # 兼容不同版本的bleak API
            try:
                service_count = len(device_services)
            except TypeError:
                # 对于BleakGATTServiceCollection，转换为列表
                service_list = list(device_services)
                service_count = len(service_list)
                device_services = service_list

            logger.info(f"发现 {service_count} 个服务")

            for i, service in enumerate(device_services, 1):
                service_uuid = service.uuid
                services.append(service_uuid)
                logger.debug(f"服务 {i}: {service_uuid} ({getattr(service, 'description', 'Unknown')})")

            return services
        except Exception as e:
            logger.warning(f"获取设备服务失败: {str(e)}")
            return []

    def is_connected(self, device_address: str) -> bool:
        """检查设备是否已连接"""
        client = self._connected_clients.get(device_address)
        if client is None:
            return False
        return client.is_connected

    def get_connected_devices(self) -> List[Dict[str, Any]]:
        """获取所有已连接设备的信息"""
        connected_devices = []
        for address, info in self._connection_info.items():
            if self.is_connected(address):
                connected_devices.append(info.copy())
            else:
                # 清理已断开的连接
                self._cleanup_disconnected_device(address)
        return connected_devices

    def get_connection_info(self, device_address: str) -> Optional[Dict[str, Any]]:
        """获取特定设备的连接信息"""
        if not self.is_connected(device_address):
            return None
        return self._connection_info.get(device_address, {}).copy()

    def _cleanup_disconnected_device(self, device_address: str):
        """清理已断开连接的设备信息"""
        self._connected_clients.pop(device_address, None)
        self._connection_info.pop(device_address, None)
        logger.debug(f"清理断开连接的设备: {device_address}")

    async def disconnect_all(self):
        """断开所有连接的设备"""
        logger.info("断开所有设备连接")
        disconnect_tasks = []

        for address in list(self._connected_clients.keys()):
            task = self.disconnect_device(address)
            disconnect_tasks.append(task)

        if disconnect_tasks:
            await asyncio.gather(*disconnect_tasks, return_exceptions=True)

    async def get_device_client(self, device_address: str) -> Optional[BleakClient]:
        """获取设备的BleakClient实例（用于高级操作）"""
        if not self.is_connected(device_address):
            return None
        return self._connected_clients.get(device_address)