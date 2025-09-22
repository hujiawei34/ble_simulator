"""BLE GATT Server Implementation"""
import dbus
import dbus.exceptions
import dbus.service
from typing import Optional, Dict, Any, List, Callable
import threading
import time

from src.python.utils.log_util import LogUtil

logger = LogUtil.get_logger('gatt_server')

BLUEZ_SERVICE_NAME = 'org.bluez'
GATT_MANAGER_IFACE = 'org.bluez.GattManager1'
GATT_SERVICE_IFACE = 'org.bluez.GattService1'
GATT_CHARACTERISTIC_IFACE = 'org.bluez.GattCharacteristic1'
GATT_DESCRIPTOR_IFACE = 'org.bluez.GattDescriptor1'

# D-Bus 接口常量
OBJECT_MANAGER_IFACE = 'org.freedesktop.DBus.ObjectManager'
PROPERTIES_IFACE = 'org.freedesktop.DBus.Properties'


class Characteristic(dbus.service.Object):
    """GATT特征值基类"""

    def __init__(self, bus: dbus.SystemBus, index: int, uuid: str, flags: List[str], service):
        """
        初始化特征值

        Args:
            bus: D-Bus系统总线
            index: 特征值索引
            uuid: 特征值UUID
            flags: 特征值标志
            service: 所属服务
        """
        self.path = service.path + '/char' + str(index)
        self.bus = bus
        self.uuid = uuid
        self.service = service
        self.flags = flags
        self.value = []
        self.notifying = False
        self.subscribers = []

        dbus.service.Object.__init__(self, bus, self.path)
        logger.debug(f"创建特征值: {self.path}, UUID: {uuid}")

    def get_properties(self) -> Dict[str, Any]:
        """获取特征值属性"""
        return {
            GATT_CHARACTERISTIC_IFACE: {
                'Service': self.service.get_path(),
                'UUID': self.uuid,
                'Flags': self.flags,
                'Value': dbus.Array(self.value, signature=dbus.Signature('y'))
            }
        }

    def get_path(self) -> dbus.ObjectPath:
        """获取对象路径"""
        return dbus.ObjectPath(self.path)

    @dbus.service.method(GATT_CHARACTERISTIC_IFACE,
                         in_signature='a{sv}', out_signature='ay')
    def ReadValue(self, options):
        """读取特征值"""
        logger.debug(f"读取特征值: {self.uuid}")
        return dbus.Array(self.value, signature=dbus.Signature('y'))

    @dbus.service.method(GATT_CHARACTERISTIC_IFACE, in_signature='aya{sv}')
    def WriteValue(self, value, options):
        """写入特征值"""
        logger.debug(f"写入特征值: {self.uuid}, value: {bytes(value)}")
        self.value = value

    @dbus.service.method(GATT_CHARACTERISTIC_IFACE)
    def StartNotify(self):
        """开始通知"""
        if self.notifying:
            logger.warning(f"特征值 {self.uuid} 已在通知中")
            return

        self.notifying = True
        logger.info(f"开始通知特征值: {self.uuid}")

    @dbus.service.method(GATT_CHARACTERISTIC_IFACE)
    def StopNotify(self):
        """停止通知"""
        if not self.notifying:
            logger.warning(f"特征值 {self.uuid} 未在通知中")
            return

        self.notifying = False
        logger.info(f"停止通知特征值: {self.uuid}")

    @dbus.service.signal(dbus.PROPERTIES_IFACE, signature='sa{sv}as')
    def PropertiesChanged(self, interface, changed, invalidated):
        """属性变化信号"""
        pass

    def set_value(self, value: bytes):
        """设置特征值并触发通知"""
        self.value = list(value)
        if self.notifying:
            self.PropertiesChanged(
                GATT_CHARACTERISTIC_IFACE,
                {'Value': dbus.Array(self.value, signature=dbus.Signature('y'))},
                []
            )
            logger.debug(f"通知特征值更新: {self.uuid}")

    @dbus.service.method(PROPERTIES_IFACE,
                         in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        """获取所有属性"""
        if interface != GATT_CHARACTERISTIC_IFACE:
            raise dbus.exceptions.DBusException(
                'org.freedesktop.DBus.Error.InvalidArgs',
                'Invalid interface'
            )
        return self.get_properties()[GATT_CHARACTERISTIC_IFACE]


class GripDataCharacteristic(Characteristic):
    """握力数据特征值"""

    GRIP_DATA_UUID = '12345678-1234-5678-9abc-123456789abd'

    def __init__(self, bus: dbus.SystemBus, index: int, service):
        """初始化握力数据特征值"""
        super().__init__(
            bus, index, self.GRIP_DATA_UUID,
            ['read', 'notify'], service
        )
        # 初始握力数据
        initial_data = "L1:100 L2:100 L3:100 R1:100 R2:100 R3:100 Score:80"
        self.set_value(initial_data.encode('utf-8'))
        logger.info("握力数据特征值初始化完成")

    def update_grip_data(self, grip_data: str):
        """更新握力数据"""
        logger.debug(f"更新握力数据: {grip_data}")
        self.set_value(grip_data.encode('utf-8'))


class DeviceInfoCharacteristic(Characteristic):
    """设备信息特征值"""

    DEVICE_INFO_UUID = '12345678-1234-5678-9abc-123456789abe'

    def __init__(self, bus: dbus.SystemBus, index: int, service):
        """初始化设备信息特征值"""
        super().__init__(
            bus, index, self.DEVICE_INFO_UUID,
            ['read'], service
        )
        # 设备信息
        device_info = {
            "model": "Support Frame SF-001",
            "manufacturer": "BLE Simulator Inc",
            "version": "1.0.0"
        }
        info_str = f"Model:{device_info['model']};Manufacturer:{device_info['manufacturer']};Version:{device_info['version']}"
        self.set_value(info_str.encode('utf-8'))
        logger.info("设备信息特征值初始化完成")


class ControlCharacteristic(Characteristic):
    """控制特征值"""

    CONTROL_UUID = '12345678-1234-5678-9abc-123456789abf'

    def __init__(self, bus: dbus.SystemBus, index: int, service):
        """初始化控制特征值"""
        super().__init__(
            bus, index, self.CONTROL_UUID,
            ['write'], service
        )
        self.control_callback = None
        logger.info("控制特征值初始化完成")

    def set_control_callback(self, callback: Callable[[str], None]):
        """设置控制回调函数"""
        self.control_callback = callback

    @dbus.service.method(GATT_CHARACTERISTIC_IFACE, in_signature='aya{sv}')
    def WriteValue(self, value, options):
        """写入控制命令"""
        super().WriteValue(value, options)
        command = bytes(value).decode('utf-8')
        logger.info(f"收到控制命令: {command}")

        if self.control_callback:
            try:
                self.control_callback(command)
            except Exception as e:
                logger.error(f"执行控制命令失败: {str(e)}")


class SupportFrameService(dbus.service.Object):
    """辅助架服务"""

    PATH_BASE = '/org/bluez/service'
    SERVICE_UUID = '12345678-1234-5678-9abc-123456789abc'

    def __init__(self, bus: dbus.SystemBus, index: int = 0):
        """初始化辅助架服务"""
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        self.uuid = self.SERVICE_UUID
        self.primary = True
        self.characteristics = []

        dbus.service.Object.__init__(self, bus, self.path)

        # 添加特征值
        self.grip_data_char = GripDataCharacteristic(bus, 0, self)
        self.device_info_char = DeviceInfoCharacteristic(bus, 1, self)
        self.control_char = ControlCharacteristic(bus, 2, self)

        self.characteristics = [
            self.grip_data_char,
            self.device_info_char,
            self.control_char
        ]

        logger.info(f"辅助架服务初始化完成: {self.path}")

    def get_properties(self) -> Dict[str, Any]:
        """获取服务属性"""
        return {
            GATT_SERVICE_IFACE: {
                'UUID': self.uuid,
                'Primary': self.primary,
                'Characteristics': dbus.Array(
                    [char.get_path() for char in self.characteristics],
                    signature=dbus.Signature('o')
                )
            }
        }

    def get_path(self) -> dbus.ObjectPath:
        """获取对象路径"""
        return dbus.ObjectPath(self.path)

    @dbus.service.method(PROPERTIES_IFACE,
                         in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        """获取所有属性"""
        if interface != GATT_SERVICE_IFACE:
            raise dbus.exceptions.DBusException(
                'org.freedesktop.DBus.Error.InvalidArgs',
                'Invalid interface'
            )
        return self.get_properties()[GATT_SERVICE_IFACE]

    def update_grip_data(self, grip_data: str):
        """更新握力数据"""
        self.grip_data_char.update_grip_data(grip_data)

    def set_control_callback(self, callback: Callable[[str], None]):
        """设置控制回调"""
        self.control_char.set_control_callback(callback)


class Application(dbus.service.Object):
    """GATT应用程序"""

    def __init__(self, bus: dbus.SystemBus):
        """初始化GATT应用程序"""
        self.path = '/'
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)

        # 添加辅助架服务
        self.support_frame_service = SupportFrameService(bus, 0)
        self.services.append(self.support_frame_service)

        logger.info("GATT应用程序初始化完成")

    def get_path(self) -> dbus.ObjectPath:
        """获取对象路径"""
        return dbus.ObjectPath(self.path)

    @dbus.service.method(OBJECT_MANAGER_IFACE,
                         out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        """获取管理的对象"""
        response = {}

        for service in self.services:
            response[service.get_path()] = service.get_properties()
            for char in service.characteristics:
                response[char.get_path()] = char.get_properties()

        return response


class GattServer:
    """GATT服务器"""

    def __init__(self):
        """初始化GATT服务器"""
        self.bus = None
        self.adapter = None
        self.service_manager = None
        self.application = None
        self.is_running = False

        logger.info("GATT服务器初始化")

    def initialize(self, adapter_path: str = '/org/bluez/hci0') -> bool:
        """
        初始化GATT服务器

        Args:
            adapter_path: 蓝牙适配器路径

        Returns:
            初始化是否成功
        """
        try:
            # 获取系统D-Bus
            self.bus = dbus.SystemBus()

            # 获取服务管理器
            self.service_manager = dbus.Interface(
                self.bus.get_object(BLUEZ_SERVICE_NAME, adapter_path),
                GATT_MANAGER_IFACE
            )

            logger.info(f"GATT服务器初始化成功，适配器: {adapter_path}")
            return True

        except Exception as e:
            logger.error(f"GATT服务器初始化失败: {str(e)}")
            return False

    def start_server(self) -> bool:
        """
        启动GATT服务器

        Returns:
            服务器是否启动成功
        """
        if self.is_running:
            logger.warning("GATT服务器已在运行中")
            return True

        try:
            logger.info("开始启动GATT服务器...")

            # 创建GATT应用程序
            logger.debug("创建GATT应用程序...")
            self.application = Application(self.bus)
            logger.debug(f"GATT应用程序创建成功，路径: {self.application.get_path()}")

            # 注册应用程序
            logger.debug("注册GATT应用程序到BlueZ...")
            self.service_manager.RegisterApplication(
                self.application.get_path(),
                {},
                reply_handler=self._register_app_cb,
                error_handler=self._register_app_error_cb
            )

            self.is_running = True
            logger.info("GATT服务器启动成功")
            return True

        except Exception as e:
            logger.error(f"启动GATT服务器失败: {str(e)}", exc_info=True)
            return False

    def stop_server(self) -> bool:
        """
        停止GATT服务器

        Returns:
            服务器是否停止成功
        """
        if not self.is_running or not self.application:
            logger.warning("GATT服务器未在运行")
            return True

        try:
            # 取消注册应用程序
            self.service_manager.UnregisterApplication(self.application.get_path())

            # 移除应用程序对象
            self.application.remove_from_connection()
            self.application = None

            self.is_running = False
            logger.info("GATT服务器停止成功")
            return True

        except Exception as e:
            logger.error(f"停止GATT服务器失败: {str(e)}")
            return False

    def update_grip_data(self, grip_data: str) -> bool:
        """
        更新握力数据

        Args:
            grip_data: 握力数据字符串

        Returns:
            更新是否成功
        """
        if not self.is_running or not self.application:
            logger.warning("GATT服务器未运行，无法更新数据")
            return False

        try:
            self.application.support_frame_service.update_grip_data(grip_data)
            return True
        except Exception as e:
            logger.error(f"更新握力数据失败: {str(e)}")
            return False

    def set_control_callback(self, callback: Callable[[str], None]):
        """设置控制回调函数"""
        if self.application:
            self.application.support_frame_service.set_control_callback(callback)

    def is_server_running(self) -> bool:
        """检查服务器是否运行中"""
        return self.is_running

    def get_status(self) -> Dict[str, Any]:
        """获取服务器状态"""
        return {
            "is_running": self.is_running,
            "service_manager_available": self.service_manager is not None,
            "application_active": self.application is not None
        }

    def _register_app_cb(self):
        """应用程序注册成功回调"""
        logger.info("✅ GATT应用程序注册成功！服务现在可用")

    def _register_app_error_cb(self, error):
        """应用程序注册失败回调"""
        logger.error(f"❌ GATT应用程序注册失败: {str(error)}")
        logger.error(f"错误类型: {type(error).__name__}")
        self.is_running = False

    def shutdown(self):
        """关闭GATT服务器"""
        logger.info("关闭GATT服务器")
        if self.is_running:
            self.stop_server()