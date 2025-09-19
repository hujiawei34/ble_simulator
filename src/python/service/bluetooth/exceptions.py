"""Bluetooth Related Exceptions"""


class BluetoothException(Exception):
    """蓝牙操作基础异常"""
    pass


class BluetoothAdapterNotFoundError(BluetoothException):
    """蓝牙适配器未找到异常"""
    def __init__(self, message="蓝牙适配器未找到或未启用"):
        self.message = message
        super().__init__(self.message)


class BluetoothScanError(BluetoothException):
    """蓝牙扫描异常"""
    def __init__(self, message="蓝牙扫描失败"):
        self.message = message
        super().__init__(self.message)


class BluetoothConnectionError(BluetoothException):
    """蓝牙连接异常"""
    def __init__(self, device_address, message="蓝牙连接失败"):
        self.device_address = device_address
        self.message = f"{message}: {device_address}"
        super().__init__(self.message)


class BluetoothPermissionError(BluetoothException):
    """蓝牙权限异常"""
    def __init__(self, message="蓝牙操作权限不足"):
        self.message = message
        super().__init__(self.message)


class DeviceNotFoundError(BluetoothException):
    """设备未找到异常"""
    def __init__(self, device_address, message="设备未找到"):
        self.device_address = device_address
        self.message = f"{message}: {device_address}"
        super().__init__(self.message)


class DeviceAlreadyConnectedError(BluetoothException):
    """设备已连接异常"""
    def __init__(self, device_address, message="设备已连接"):
        self.device_address = device_address
        self.message = f"{message}: {device_address}"
        super().__init__(self.message)