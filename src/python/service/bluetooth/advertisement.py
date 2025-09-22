"""BLE Advertisement Manager"""
import dbus
import dbus.exceptions
import dbus.service
from typing import Optional, Dict, Any
import uuid

from src.python.utils.log_util import LogUtil

logger = LogUtil.get_logger('advertisement')

BLUEZ_SERVICE_NAME = 'org.bluez'
BLUEZ_OBJECT_PATH = '/org/bluez'
LE_ADVERTISEMENT_IFACE = 'org.bluez.LEAdvertisement1'
LE_ADVERTISING_MANAGER_IFACE = 'org.bluez.LEAdvertisingManager1'

# D-Bus 接口常量
PROPERTIES_IFACE = 'org.freedesktop.DBus.Properties'


class Advertisement(dbus.service.Object):
    """BLE广播对象"""

    PATH_BASE = '/org/bluez/advertisement'

    def __init__(self, bus: dbus.SystemBus, index: int, ad_type: str = 'connectable'):
        """
        初始化广播对象

        Args:
            bus: D-Bus系统总线
            index: 广播索引
            ad_type: 广播类型
        """
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        self.ad_type = ad_type
        self.service_uuids = []
        self.manufacturer_data = {}
        self.service_data = {}
        self.local_name = ''
        self.include_tx_power = False
        self.data = {}

        dbus.service.Object.__init__(self, bus, self.path)
        logger.info(f"创建广播对象: {self.path}")

    def get_properties(self) -> Dict[str, Any]:
        """获取广播属性"""
        properties = {
            'Type': dbus.String(self.ad_type),
        }

        # 只在有内容时添加各个属性
        if self.service_uuids:
            properties['ServiceUUIDs'] = dbus.Array(self.service_uuids, signature='s')

        if self.include_tx_power:
            properties['IncludeTxPower'] = dbus.Boolean(self.include_tx_power)

        if self.manufacturer_data:
            properties['ManufacturerData'] = self.manufacturer_data

        if self.service_data:
            properties['ServiceData'] = self.service_data

        if self.local_name:
            properties['LocalName'] = dbus.String(self.local_name)

        logger.debug(f"广播属性: {properties}")
        return {LE_ADVERTISEMENT_IFACE: properties}

    def get_path(self) -> str:
        """获取对象路径"""
        return dbus.ObjectPath(self.path)

    def add_service_uuid(self, uuid_str: str):
        """添加服务UUID"""
        if uuid_str not in self.service_uuids:
            self.service_uuids.append(uuid_str)
            logger.info(f"✅ 添加服务UUID: {uuid_str}")
            logger.info(f"当前服务UUID列表: {self.service_uuids}")

    def add_manufacturer_data(self, manuf_code: int, data: bytes):
        """添加制造商数据"""
        self.manufacturer_data[manuf_code] = dbus.Array(data, signature=dbus.Signature('y'))
        logger.info(f"✅ 添加制造商数据: {manuf_code} -> {data.hex()}")

    def add_service_data(self, uuid_str: str, data: bytes):
        """添加服务数据"""
        self.service_data[uuid_str] = dbus.Array(data, signature=dbus.Signature('y'))
        logger.info(f"✅ 添加服务数据: {uuid_str} -> {data.hex()}")

    def set_local_name(self, name: str):
        """设置本地名称"""
        self.local_name = name
        logger.info(f"✅ 设置设备名称: {name}")

    @dbus.service.method(LE_ADVERTISEMENT_IFACE,
                         in_signature='', out_signature='')
    def Release(self):
        """释放广播"""
        logger.info(f"🔄 BlueZ请求释放广播: {self.path}")

    @dbus.service.method(PROPERTIES_IFACE,
                         in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        """获取所有属性"""
        logger.info(f"🔍 BlueZ请求获取广播属性，接口: {interface}")
        if interface != LE_ADVERTISEMENT_IFACE:
            logger.error(f"❌ 无效接口: {interface}，期望: {LE_ADVERTISEMENT_IFACE}")
            raise dbus.exceptions.DBusException(
                'org.freedesktop.DBus.Error.InvalidArgs',
                'Invalid interface'
            )

        properties = self.get_properties()[LE_ADVERTISEMENT_IFACE]
        logger.info(f"📋 返回广播属性: {properties}")
        return properties


class SupportFrameAdvertisement(Advertisement):
    """辅助架设备广播"""

    def __init__(self, bus: dbus.SystemBus, index: int = 0):
        """初始化辅助架广播"""
        logger.info("🚀 开始创建辅助架广播对象...")

        try:
            # 尝试使用'peripheral'作为广播类型
            super().__init__(bus, index, 'peripheral')
            logger.info("✅ 广播基类初始化成功")

            # 设置设备信息 - 先尝试最简单的配置
            logger.info("🏷️ 设置设备名称...")
            self.set_local_name('SupportFrame')

            # 暂时注释掉其他属性，先测试最基本的广播
            # logger.info("⚡ 设置发射功率...")
            # self.include_tx_power = True

            # 暂时注释掉UUID，先测试基本广播
            # logger.info("🔗 添加心率服务UUID...")
            # self.add_service_uuid('0000180d-0000-1000-8000-00805f9b34fb')  # 心率服务

            logger.info("✅ 辅助架设备广播初始化完成（简化版本）")

        except Exception as e:
            logger.error(f"❌ 广播对象创建失败: {str(e)}", exc_info=True)
            raise


class AdvertisementManager:
    """广播管理器"""

    def __init__(self):
        """初始化广播管理器"""
        self.bus = None
        self.adapter = None
        self.adv_manager = None
        self.advertisement = None
        self.is_advertising = False

        logger.info("广播管理器初始化")

    def initialize(self, adapter_path: str = '/org/bluez/hci0') -> bool:
        """
        初始化广播管理器

        Args:
            adapter_path: 蓝牙适配器路径

        Returns:
            初始化是否成功
        """
        try:
            logger.info(f"开始初始化广播管理器，适配器路径: {adapter_path}")

            # 检查当前用户权限
            import os
            current_user = os.getuid()
            logger.info(f"当前用户UID: {current_user} (root=0)")
            if current_user != 0:
                logger.warning("⚠️ 当前不是root用户，BLE广播功能可能需要root权限")

            # 获取系统D-Bus
            logger.debug("获取系统D-Bus...")
            self.bus = dbus.SystemBus()
            logger.debug("系统D-Bus获取成功")

            # 检查BlueZ服务是否可用
            try:
                bluez_object = self.bus.get_object(BLUEZ_SERVICE_NAME, BLUEZ_OBJECT_PATH)
                logger.info("✅ BlueZ服务连接成功")
            except Exception as e:
                logger.error(f"❌ BlueZ服务连接失败: {str(e)}")
                return False

            # 获取蓝牙适配器
            logger.debug(f"获取蓝牙适配器对象: {adapter_path}")
            adapter_obj = self.bus.get_object(BLUEZ_SERVICE_NAME, adapter_path)
            logger.debug("蓝牙适配器对象获取成功")

            self.adapter = dbus.Interface(
                adapter_obj,
                'org.freedesktop.DBus.Properties'
            )
            logger.debug("蓝牙适配器接口创建成功")

            # 获取广播管理器
            logger.debug(f"获取广播管理器接口: {LE_ADVERTISING_MANAGER_IFACE}")
            self.adv_manager = dbus.Interface(
                adapter_obj,
                LE_ADVERTISING_MANAGER_IFACE
            )
            logger.debug("广播管理器接口创建成功")

            # 检查广播管理器支持的功能
            try:
                properties_interface = dbus.Interface(adapter_obj, 'org.freedesktop.DBus.Properties')
                supported_instances = properties_interface.Get(LE_ADVERTISING_MANAGER_IFACE, 'SupportedInstances')
                active_instances = properties_interface.Get(LE_ADVERTISING_MANAGER_IFACE, 'ActiveInstances')
                supported_includes = properties_interface.Get(LE_ADVERTISING_MANAGER_IFACE, 'SupportedIncludes')

                logger.info(f"📊 广播管理器功能:")
                logger.info(f"  - 支持的广播实例数: {supported_instances} (类型: {type(supported_instances)})")
                logger.info(f"  - 当前活跃实例数: {active_instances} (类型: {type(active_instances)})")
                logger.info(f"  - 支持的Include属性: {list(supported_includes)}")

                if active_instances >= supported_instances:
                    logger.warning(f"⚠️ 广播实例已满 ({active_instances}/{supported_instances})")

            except Exception as e:
                logger.warning(f"获取广播管理器属性失败: {str(e)}")

            logger.info(f"广播管理器初始化成功，适配器: {adapter_path}")
            return True

        except Exception as e:
            logger.error(f"广播管理器初始化失败: {str(e)}", exc_info=True)
            return False

    def start_advertising(self) -> bool:
        """
        开始广播

        Returns:
            广播是否启动成功
        """
        if self.is_advertising:
            logger.warning("广播已在运行中")
            return True

        try:
            logger.info("开始启动BLE广播...")

            # 再次检查权限
            import os
            if os.getuid() != 0:
                logger.error("❌ BLE广播需要root权限，请使用sudo运行程序")
                return False

            # 创建辅助架广播
            logger.debug("创建广播对象...")
            self.advertisement = SupportFrameAdvertisement(self.bus, 0)
            logger.debug(f"广播对象创建成功，路径: {self.advertisement.get_path()}")

            # 获取并打印广播属性用于调试
            ad_properties = self.advertisement.get_properties()
            logger.info(f"准备注册的广播属性: {ad_properties}")

            # 详细验证广播属性
            props = ad_properties.get(LE_ADVERTISEMENT_IFACE, {})
            logger.info(f"🔍 验证广播属性:")
            logger.info(f"  - Type: {props.get('Type')} (D-Bus类型: {type(props.get('Type'))})")
            logger.info(f"  - ServiceUUIDs: {props.get('ServiceUUIDs')} (D-Bus类型: {type(props.get('ServiceUUIDs'))})")
            logger.info(f"  - LocalName: {props.get('LocalName')} (D-Bus类型: {type(props.get('LocalName'))})")
            logger.info(f"  - IncludeTxPower: {props.get('IncludeTxPower')} (D-Bus类型: {type(props.get('IncludeTxPower'))})")

            # 检查UUID格式
            service_uuids = props.get('ServiceUUIDs')
            if service_uuids:
                for uuid_val in service_uuids:
                    logger.info(f"  - UUID值: '{uuid_val}' (长度: {len(str(uuid_val))})")

            # 注册广播
            logger.debug("注册广播到BlueZ...")
            self.adv_manager.RegisterAdvertisement(
                self.advertisement.get_path(),
                {},
                reply_handler=self._register_ad_cb,
                error_handler=self._register_ad_error_cb
            )

            # 注意：不要在这里设置 is_advertising = True
            # 应该在 _register_ad_cb 回调中设置
            logger.info("广播注册请求已发送，等待BlueZ响应...")
            return True

        except Exception as e:
            logger.error(f"启动广播失败: {str(e)}", exc_info=True)
            return False

    def stop_advertising(self) -> bool:
        """
        停止广播

        Returns:
            广播是否停止成功
        """
        if not self.is_advertising or not self.advertisement:
            logger.warning("广播未在运行")
            return True

        try:
            # 取消注册广播
            self.adv_manager.UnregisterAdvertisement(self.advertisement.get_path())

            # 移除广播对象
            self.advertisement.remove_from_connection()
            self.advertisement = None

            self.is_advertising = False
            logger.info("广播停止成功")
            return True

        except Exception as e:
            logger.error(f"停止广播失败: {str(e)}")
            return False

    def is_running(self) -> bool:
        """检查广播是否运行中"""
        return self.is_advertising

    def get_status(self) -> Dict[str, Any]:
        """获取广播状态"""
        return {
            "is_advertising": self.is_advertising,
            "adapter_available": self.adapter is not None,
            "advertisement_active": self.advertisement is not None
        }

    def _register_ad_cb(self):
        """广播注册成功回调"""
        logger.info("✅ 广播注册成功！设备现在可以被发现")
        logger.info("🔍 请在手机nRF Connect中搜索设备名: SupportFrame")
        logger.info("🔍 或搜索心率服务UUID: 0000180d-0000-1000-8000-00805f9b34fb")

    def _register_ad_error_cb(self, error):
        """广播注册失败回调"""
        logger.error(f"❌ 广播注册失败: {str(error)}")
        logger.error(f"错误类型: {type(error).__name__}")
        logger.error(f"错误详情: {error}")

        # 输出当前广播属性用于调试
        if self.advertisement:
            try:
                ad_properties = self.advertisement.get_properties()
                logger.error(f"失败的广播属性: {ad_properties}")

                # 详细分析每个属性
                props = ad_properties.get(LE_ADVERTISEMENT_IFACE, {})
                logger.error(f"Type: {props.get('Type')} (类型: {type(props.get('Type'))})")
                logger.error(f"ServiceUUIDs: {props.get('ServiceUUIDs')} (类型: {type(props.get('ServiceUUIDs'))})")
                logger.error(f"LocalName: {props.get('LocalName')} (类型: {type(props.get('LocalName'))})")
                logger.error(f"IncludeTxPower: {props.get('IncludeTxPower')} (类型: {type(props.get('IncludeTxPower'))})")

                # 检查D-Bus签名
                for key, value in props.items():
                    if hasattr(value, 'signature'):
                        logger.error(f"{key} D-Bus签名: {value.signature}")

            except Exception as e:
                logger.error(f"获取广播属性失败: {str(e)}")

        self.is_advertising = False

    def shutdown(self):
        """关闭广播管理器"""
        logger.info("关闭广播管理器")
        if self.is_advertising:
            self.stop_advertising()