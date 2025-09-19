"""FastAPI Pydantic Models"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class DeviceInfo(BaseModel):
    """BLE设备信息模型"""
    name: Optional[str] = Field(None, description="设备名称")
    address: str = Field(..., description="设备MAC地址")
    rssi: Optional[int] = Field(None, description="信号强度")
    services: List[str] = Field(default_factory=list, description="服务UUID列表")
    manufacturer_data: Dict[str, Any] = Field(default_factory=dict, description="制造商数据")

class ScanRequest(BaseModel):
    """扫描请求模型"""
    duration: int = Field(10, ge=1, le=60, description="扫描持续时间(秒)")
    filter_name: Optional[str] = Field(None, description="设备名称过滤")
    filter_services: List[str] = Field(default_factory=list, description="服务UUID过滤")

class ScanResponse(BaseModel):
    """扫描响应模型"""
    status: str = Field(..., description="扫描状态")
    devices: List[DeviceInfo] = Field(default_factory=list, description="发现的设备")
    scan_time: datetime = Field(default_factory=datetime.now, description="扫描时间")
    duration: int = Field(..., description="扫描持续时间")

class ConnectionRequest(BaseModel):
    """连接请求模型"""
    device_address: str = Field(..., description="设备MAC地址")
    timeout: int = Field(30, ge=5, le=120, description="连接超时时间(秒)")

class ConnectionResponse(BaseModel):
    """连接响应模型"""
    status: str = Field(..., description="连接状态")
    device_address: str = Field(..., description="设备MAC地址")
    connected: bool = Field(..., description="连接状态")
    connection_time: Optional[datetime] = Field(None, description="连接时间")
    services: List[str] = Field(default_factory=list, description="可用服务")

class ApiResponse(BaseModel):
    """通用API响应模型"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")

class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field("healthy", description="服务状态")
    service: str = Field("FastAPI BLE Simulator", description="服务名称")
    version: str = Field("1.0.0", description="版本号")
    timestamp: datetime = Field(default_factory=datetime.now, description="检查时间")