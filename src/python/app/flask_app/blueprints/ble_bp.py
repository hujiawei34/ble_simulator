"""BLE Operations Blueprint"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.python.utils.log_util import LogUtil

ble_bp = Blueprint('ble', __name__, url_prefix='/ble')
logger = LogUtil.get_logger('ble_blueprint')

@ble_bp.route('/scan')
def scan():
    """BLE设备扫描页面"""
    logger.info("访问BLE扫描页面")
    return render_template('ble/scan.html', title='BLE Scan')

@ble_bp.route('/connect')
def connect_page():
    """BLE连接页面"""
    logger.info("访问BLE连接页面")
    return render_template('ble/connect.html', title='BLE Connect')

@ble_bp.route('/status')
def status():
    """BLE状态信息"""
    logger.info("获取BLE状态信息")

    # 模拟状态数据
    status_data = {
        'bluetooth_enabled': True,
        'scanning': False,
        'connected_devices': [],
        'available_adapters': ['hci0']
    }

    return jsonify(status_data)