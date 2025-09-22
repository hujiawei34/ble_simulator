"""BLE Peripheral Service Layer"""
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import threading
import time
import gi
import dbus
import dbus.mainloop.glib

# 需要导入GLib用于事件循环
gi.require_version('GLib', '2.0')
from gi.repository import GLib

from src.python.utils.log_util import LogUtil
from .bluetooth.advertisement import AdvertisementManager
from .bluetooth.gatt_server import GattServer
from .bluetooth.grip_simulator import GripDataManager

logger = LogUtil.get_logger('ble_peripheral_service')


class BLEPeripheralService:
    """BLE外围设备服务"""

    def __init__(self):
        """初始化BLE外围设备服务"""
        self.advertisement_manager = AdvertisementManager()
        self.gatt_server = GattServer()
        self.grip_data_manager = GripDataManager()

        self.is_running = False
        self.is_initialized = False
        self.connected_clients = []

        # GLib事件循环
        self.mainloop = None
        self.mainloop_thread = None

        # 统计信息
        self.start_time = None
        self.data_sent_count = 0

        logger.info("BLE外围设备服务初始化完成")

    def initialize(self, adapter_path: str = '/org/bluez/hci0') -> bool:
        """
        初始化BLE外围设备服务

        Args:
            adapter_path: 蓝牙适配器路径

        Returns:
            初始化是否成功
        """
        try:
            logger.info(f"开始初始化BLE外围设备服务，适配器路径: {adapter_path}")

            # 设置D-Bus主循环
            logger.info("设置D-Bus主循环...")
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            logger.info("D-Bus主循环设置成功")

            # 初始化广播管理器
            logger.info("正在初始化广播管理器...")
            if not self.advertisement_manager.initialize(adapter_path):
                logger.error("广播管理器初始化失败")
                return False
            logger.info("广播管理器初始化成功")

            # 初始化GATT服务器
            logger.info("正在初始化GATT服务器...")
            if not self.gatt_server.initialize(adapter_path):
                logger.error("GATT服务器初始化失败")
                return False
            logger.info("GATT服务器初始化成功")

            # 设置握力数据回调
            logger.info("设置握力数据回调...")
            self.grip_data_manager.set_data_callback(self._on_grip_data_update)

            # 设置控制命令回调
            logger.info("设置控制命令回调...")
            self.gatt_server.set_control_callback(self._on_control_command)

            self.is_initialized = True
            logger.info(f"BLE外围设备服务初始化成功，适配器: {adapter_path}")
            return True

        except Exception as e:
            logger.error(f"BLE外围设备服务初始化失败: {str(e)}", exc_info=True)
            return False

    def start_peripheral(self) -> Dict[str, Any]:
        """
        启动外围设备模式

        Returns:
            启动结果
        """
        if not self.is_initialized:
            return {
                "success": False,
                "message": "服务未初始化，请先调用initialize()"
            }

        if self.is_running:
            return {
                "success": False,
                "message": "外围设备模式已在运行中"
            }

        try:
            logger.info("开始启动BLE外围设备模式...")

            # 如果未初始化，先初始化（包含D-Bus主循环设置）
            if not self.is_initialized:
                logger.info("服务未初始化，先进行初始化...")
                if not self.initialize():
                    logger.error("服务初始化失败")
                    return {
                        "success": False,
                        "message": "服务初始化失败"
                    }

            # 启动GLib事件循环
            logger.info("正在启动GLib事件循环...")
            if not self._start_mainloop():
                logger.error("GLib事件循环启动失败")
                return {
                    "success": False,
                    "message": "GLib事件循环启动失败"
                }
            logger.info("GLib事件循环启动成功")

            # 启动GATT服务器
            logger.info("正在启动GATT服务器...")
            if not self.gatt_server.start_server():
                logger.error("GATT服务器启动失败")
                return {
                    "success": False,
                    "message": "GATT服务器启动失败"
                }
            logger.info("GATT服务器启动成功")

            # 启动广播
            logger.info("正在启动BLE广播...")
            if not self.advertisement_manager.start_advertising():
                logger.error("BLE广播启动失败")
                self.gatt_server.stop_server()
                return {
                    "success": False,
                    "message": "BLE广播启动失败"
                }
            logger.info("BLE广播启动成功")

            # 启动握力数据模拟器
            logger.info("正在启动握力数据模拟器...")
            if not self.grip_data_manager.start():
                logger.error("握力数据模拟器启动失败")
                self.advertisement_manager.stop_advertising()
                self.gatt_server.stop_server()
                return {
                    "success": False,
                    "message": "握力数据模拟器启动失败"
                }
            logger.info("握力数据模拟器启动成功")

            self.is_running = True
            self.start_time = datetime.now()
            self.data_sent_count = 0

            logger.info("BLE外围设备模式启动成功")
            return {
                "success": True,
                "message": "BLE外围设备模式启动成功",
                "start_time": self.start_time.isoformat(),
                "device_name": "Support Frame Simulator"
            }

        except Exception as e:
            logger.error(f"启动外围设备模式失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"启动失败: {str(e)}"
            }

    def stop_peripheral(self) -> Dict[str, Any]:
        """
        停止外围设备模式

        Returns:
            停止结果
        """
        if not self.is_running:
            return {
                "success": False,
                "message": "外围设备模式未在运行"
            }

        try:
            # 停止握力数据模拟器
            self.grip_data_manager.stop()

            # 停止广播
            self.advertisement_manager.stop_advertising()

            # 停止GATT服务器
            self.gatt_server.stop_server()

            # 停止GLib事件循环
            self._stop_mainloop()

            self.is_running = False
            end_time = datetime.now()

            if self.start_time:
                duration = (end_time - self.start_time).total_seconds()
            else:
                duration = 0

            logger.info("BLE外围设备模式停止成功")
            return {
                "success": True,
                "message": "BLE外围设备模式停止成功",
                "stop_time": end_time.isoformat(),
                "duration_seconds": duration,
                "data_sent_count": self.data_sent_count
            }

        except Exception as e:
            logger.error(f"停止外围设备模式失败: {str(e)}")
            return {
                "success": False,
                "message": f"停止失败: {str(e)}"
            }

    def get_status(self) -> Dict[str, Any]:
        """
        获取外围设备状态

        Returns:
            状态信息
        """
        status = {
            "is_initialized": self.is_initialized,
            "is_running": self.is_running,
            "connected_clients": len(self.connected_clients),
            "data_sent_count": self.data_sent_count
        }

        if self.start_time:
            status["start_time"] = self.start_time.isoformat()
            if self.is_running:
                duration = (datetime.now() - self.start_time).total_seconds()
                status["running_duration_seconds"] = duration

        # 获取各组件状态
        status["advertisement"] = self.advertisement_manager.get_status()
        status["gatt_server"] = self.gatt_server.get_status()
        status["grip_simulator"] = self.grip_data_manager.get_status()

        return status

    def get_current_grip_data(self) -> str:
        """获取当前握力数据"""
        return self.grip_data_manager.get_current_data()

    def set_grip_data(self, data_str: str) -> Dict[str, Any]:
        """
        设置握力数据

        Args:
            data_str: 握力数据字符串

        Returns:
            设置结果
        """
        try:
            self.grip_data_manager.update_manual_data(data_str)
            logger.info(f"手动设置握力数据: {data_str}")
            return {
                "success": True,
                "message": "握力数据设置成功",
                "data": data_str
            }
        except Exception as e:
            logger.error(f"设置握力数据失败: {str(e)}")
            return {
                "success": False,
                "message": f"设置失败: {str(e)}"
            }

    def set_simulation_mode(self, mode: str) -> Dict[str, Any]:
        """
        设置模拟模式

        Args:
            mode: 模拟模式 (normal, exercise, rest)

        Returns:
            设置结果
        """
        try:
            self.grip_data_manager.set_simulation_mode(mode)
            logger.info(f"设置模拟模式: {mode}")
            return {
                "success": True,
                "message": f"模拟模式设置为: {mode}",
                "mode": mode
            }
        except Exception as e:
            logger.error(f"设置模拟模式失败: {str(e)}")
            return {
                "success": False,
                "message": f"设置失败: {str(e)}"
            }

    def get_data_history(self, limit: int = 100) -> list:
        """获取历史数据"""
        return self.grip_data_manager.get_history(limit)

    def _start_mainloop(self) -> bool:
        """启动GLib主循环"""
        try:
            if self.mainloop and self.mainloop.is_running():
                logger.warning("GLib主循环已在运行")
                return True

            self.mainloop = GLib.MainLoop()
            self.mainloop_thread = threading.Thread(target=self.mainloop.run, daemon=True)
            self.mainloop_thread.start()

            # 等待一小段时间确保循环启动
            time.sleep(0.1)

            logger.info("GLib主循环启动成功")
            return True

        except Exception as e:
            logger.error(f"启动GLib主循环失败: {str(e)}")
            return False

    def _stop_mainloop(self):
        """停止GLib主循环"""
        try:
            if self.mainloop and self.mainloop.is_running():
                self.mainloop.quit()

            if self.mainloop_thread and self.mainloop_thread.is_alive():
                self.mainloop_thread.join(timeout=2.0)

            self.mainloop = None
            self.mainloop_thread = None

            logger.info("GLib主循环停止成功")

        except Exception as e:
            logger.error(f"停止GLib主循环失败: {str(e)}")

    def _on_grip_data_update(self, data_str: str):
        """握力数据更新回调"""
        try:
            # 更新GATT服务器中的数据
            if self.gatt_server.is_server_running():
                self.gatt_server.update_grip_data(data_str)
                self.data_sent_count += 1
                logger.debug(f"更新握力数据: {data_str}")
        except Exception as e:
            logger.error(f"处理握力数据更新失败: {str(e)}")

    def _on_control_command(self, command: str):
        """控制命令回调"""
        try:
            logger.info(f"收到控制命令: {command}")

            if command.lower() == "start":
                self.grip_data_manager.start()
            elif command.lower() == "stop":
                self.grip_data_manager.stop()
            elif command.lower().startswith("mode:"):
                mode = command.split(":", 1)[1].strip()
                self.grip_data_manager.set_simulation_mode(mode)
            elif command.lower().startswith("data:"):
                data = command.split(":", 1)[1].strip()
                self.grip_data_manager.update_manual_data(data)
            else:
                logger.warning(f"未知控制命令: {command}")

        except Exception as e:
            logger.error(f"处理控制命令失败: {str(e)}")

    def shutdown(self):
        """关闭外围设备服务"""
        logger.info("关闭BLE外围设备服务")

        if self.is_running:
            self.stop_peripheral()

        # 关闭各组件
        self.grip_data_manager.shutdown()
        self.gatt_server.shutdown()
        self.advertisement_manager.shutdown()


# 全局BLE外围设备服务实例
ble_peripheral_service = BLEPeripheralService()