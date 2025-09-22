"""Grip Force Data Simulator"""
import random
import threading
import time
from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass
from datetime import datetime

from src.python.utils.log_util import LogUtil

logger = LogUtil.get_logger('grip_simulator')


@dataclass
class GripSensorData:
    """握力传感器数据"""
    left_sensors: list[int]  # L1, L2, L3
    right_sensors: list[int]  # R1, R2, R3
    score: int
    timestamp: datetime

    def to_string(self) -> str:
        """转换为字符串格式"""
        return (f"L1:{self.left_sensors[0]} L2:{self.left_sensors[1]} L3:{self.left_sensors[2]} "
                f"R1:{self.right_sensors[0]} R2:{self.right_sensors[1]} R3:{self.right_sensors[2]} "
                f"Score:{self.score}")

    @classmethod
    def from_string(cls, data_str: str) -> 'GripSensorData':
        """从字符串解析握力数据"""
        try:
            parts = data_str.strip().split(' ')
            data_dict = {}
            for part in parts:
                key, value = part.split(':')
                data_dict[key] = int(value)

            return cls(
                left_sensors=[data_dict['L1'], data_dict['L2'], data_dict['L3']],
                right_sensors=[data_dict['R1'], data_dict['R2'], data_dict['R3']],
                score=data_dict['Score'],
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"解析握力数据失败: {str(e)}")
            # 返回默认数据
            return cls(
                left_sensors=[100, 100, 100],
                right_sensors=[100, 100, 100],
                score=80,
                timestamp=datetime.now()
            )


class GripDataSimulator:
    """握力数据模拟器"""

    def __init__(self, update_interval: float = 1.0):
        """
        初始化握力数据模拟器

        Args:
            update_interval: 数据更新间隔（秒）
        """
        self.update_interval = update_interval
        self.is_running = False
        self.simulation_thread = None
        self.data_callback: Optional[Callable[[str], None]] = None
        self.current_data = GripSensorData(
            left_sensors=[100, 100, 100],
            right_sensors=[100, 100, 100],
            score=80,
            timestamp=datetime.now()
        )

        # 模拟参数
        self.simulation_mode = "normal"  # normal, exercise, rest
        self.base_values = {
            "left": [120, 115, 110],
            "right": [125, 120, 115]
        }
        self.variation_range = 30  # 变化范围
        self.trend_direction = 1  # 1为增加，-1为减少

        logger.info(f"握力数据模拟器初始化完成，更新间隔: {update_interval}秒")

    def set_data_callback(self, callback: Callable[[str], None]):
        """设置数据更新回调函数"""
        self.data_callback = callback
        logger.debug("设置数据回调函数")

    def set_simulation_mode(self, mode: str):
        """
        设置模拟模式

        Args:
            mode: 模拟模式 (normal, exercise, rest)
        """
        if mode in ["normal", "exercise", "rest"]:
            self.simulation_mode = mode
            logger.info(f"设置模拟模式: {mode}")

            # 根据模式调整基础值
            if mode == "normal":
                self.base_values = {
                    "left": [120, 115, 110],
                    "right": [125, 120, 115]
                }
                self.variation_range = 30
            elif mode == "exercise":
                self.base_values = {
                    "left": [200, 190, 180],
                    "right": [210, 200, 190]
                }
                self.variation_range = 50
            elif mode == "rest":
                self.base_values = {
                    "left": [80, 75, 70],
                    "right": [85, 80, 75]
                }
                self.variation_range = 20
        else:
            logger.warning(f"无效的模拟模式: {mode}")

    def start_simulation(self) -> bool:
        """
        启动模拟

        Returns:
            启动是否成功
        """
        if self.is_running:
            logger.warning("握力数据模拟器已在运行中")
            return True

        try:
            self.is_running = True
            self.simulation_thread = threading.Thread(target=self._simulation_loop, daemon=True)
            self.simulation_thread.start()
            logger.info("握力数据模拟器启动成功")
            return True
        except Exception as e:
            logger.error(f"启动握力数据模拟器失败: {str(e)}")
            self.is_running = False
            return False

    def stop_simulation(self) -> bool:
        """
        停止模拟

        Returns:
            停止是否成功
        """
        if not self.is_running:
            logger.warning("握力数据模拟器未在运行")
            return True

        try:
            self.is_running = False
            if self.simulation_thread and self.simulation_thread.is_alive():
                self.simulation_thread.join(timeout=2.0)
            logger.info("握力数据模拟器停止成功")
            return True
        except Exception as e:
            logger.error(f"停止握力数据模拟器失败: {str(e)}")
            return False

    def get_current_data(self) -> GripSensorData:
        """获取当前握力数据"""
        return self.current_data

    def set_manual_data(self, data: GripSensorData):
        """手动设置握力数据"""
        self.current_data = data
        if self.data_callback:
            self.data_callback(data.to_string())
        logger.debug(f"手动设置握力数据: {data.to_string()}")

    def update_data_from_string(self, data_str: str):
        """从字符串更新握力数据"""
        try:
            data = GripSensorData.from_string(data_str)
            self.set_manual_data(data)
        except Exception as e:
            logger.error(f"从字符串更新握力数据失败: {str(e)}")

    def get_status(self) -> Dict[str, Any]:
        """获取模拟器状态"""
        return {
            "is_running": self.is_running,
            "simulation_mode": self.simulation_mode,
            "current_data": self.current_data.to_string(),
            "update_interval": self.update_interval,
            "last_update": self.current_data.timestamp.isoformat()
        }

    def _simulation_loop(self):
        """模拟循环"""
        logger.info("开始握力数据模拟循环")

        while self.is_running:
            try:
                # 生成新的握力数据
                new_data = self._generate_grip_data()
                self.current_data = new_data

                # 调用回调函数
                if self.data_callback:
                    self.data_callback(new_data.to_string())

                # 等待下次更新
                time.sleep(self.update_interval)

            except Exception as e:
                logger.error(f"模拟循环中发生错误: {str(e)}")
                time.sleep(self.update_interval)

        logger.info("握力数据模拟循环结束")

    def _generate_grip_data(self) -> GripSensorData:
        """生成握力数据"""
        # 生成左手数据
        left_sensors = []
        for i, base_val in enumerate(self.base_values["left"]):
            # 添加随机变化
            variation = random.randint(-self.variation_range, self.variation_range)
            # 添加趋势变化
            trend = self.trend_direction * random.randint(0, 10)
            value = max(0, min(999, base_val + variation + trend))
            left_sensors.append(value)

        # 生成右手数据
        right_sensors = []
        for i, base_val in enumerate(self.base_values["right"]):
            # 添加随机变化
            variation = random.randint(-self.variation_range, self.variation_range)
            # 添加趋势变化
            trend = self.trend_direction * random.randint(0, 10)
            value = max(0, min(999, base_val + variation + trend))
            right_sensors.append(value)

        # 计算综合评分
        avg_left = sum(left_sensors) / len(left_sensors)
        avg_right = sum(right_sensors) / len(right_sensors)
        avg_total = (avg_left + avg_right) / 2

        # 评分映射（0-999 -> 0-100）
        score = int(min(100, max(0, (avg_total / 999) * 100)))

        # 随机改变趋势方向
        if random.random() < 0.1:  # 10%概率改变趋势
            self.trend_direction *= -1

        return GripSensorData(
            left_sensors=left_sensors,
            right_sensors=right_sensors,
            score=score,
            timestamp=datetime.now()
        )

    def set_update_interval(self, interval: float):
        """设置更新间隔"""
        if interval > 0:
            self.update_interval = interval
            logger.info(f"设置更新间隔: {interval}秒")
        else:
            logger.warning(f"无效的更新间隔: {interval}")

    def shutdown(self):
        """关闭模拟器"""
        logger.info("关闭握力数据模拟器")
        self.stop_simulation()


class GripDataManager:
    """握力数据管理器"""

    def __init__(self):
        """初始化握力数据管理器"""
        self.simulator = GripDataSimulator()
        self.data_history = []
        self.max_history_size = 1000

        logger.info("握力数据管理器初始化完成")

    def start(self) -> bool:
        """启动数据管理器"""
        return self.simulator.start_simulation()

    def stop(self) -> bool:
        """停止数据管理器"""
        return self.simulator.stop_simulation()

    def set_data_callback(self, callback: Callable[[str], None]):
        """设置数据回调"""
        def wrapper(data_str: str):
            # 记录历史数据
            self._add_to_history(data_str)
            # 调用原始回调
            callback(data_str)

        self.simulator.set_data_callback(wrapper)

    def _add_to_history(self, data_str: str):
        """添加到历史记录"""
        self.data_history.append({
            "data": data_str,
            "timestamp": datetime.now().isoformat()
        })

        # 限制历史记录大小
        if len(self.data_history) > self.max_history_size:
            self.data_history = self.data_history[-self.max_history_size:]

    def get_history(self, limit: int = 100) -> list:
        """获取历史数据"""
        return self.data_history[-limit:]

    def get_current_data(self) -> str:
        """获取当前数据"""
        return self.simulator.get_current_data().to_string()

    def set_simulation_mode(self, mode: str):
        """设置模拟模式"""
        self.simulator.set_simulation_mode(mode)

    def update_manual_data(self, data_str: str):
        """手动更新数据"""
        self.simulator.update_data_from_string(data_str)

    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        status = self.simulator.get_status()
        status.update({
            "history_count": len(self.data_history),
            "max_history_size": self.max_history_size
        })
        return status

    def shutdown(self):
        """关闭管理器"""
        logger.info("关闭握力数据管理器")
        self.simulator.shutdown()