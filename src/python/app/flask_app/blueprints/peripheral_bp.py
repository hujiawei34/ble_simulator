"""BLE Peripheral Blueprint"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.python.utils.log_util import LogUtil
from src.python.service.ble_peripheral_service import ble_peripheral_service

logger = LogUtil.get_logger('peripheral_bp')

# 创建蓝图
peripheral_bp = Blueprint('peripheral', __name__, url_prefix='/peripheral')


@peripheral_bp.route('/')
def simulator():
    """BLE设备模拟器主页"""
    logger.info("访问BLE设备模拟器页面")
    try:
        status = ble_peripheral_service.get_status()
        current_data = ble_peripheral_service.get_current_grip_data()

        return render_template('peripheral/simulator.html',
                               title="BLE设备模拟器",
                               status=status,
                               current_data=current_data)
    except Exception as e:
        logger.error(f"获取模拟器状态失败: {str(e)}")
        flash(f"获取状态失败: {str(e)}", 'error')
        return render_template('peripheral/simulator.html',
                               title="BLE设备模拟器",
                               status=None,
                               current_data="")


@peripheral_bp.route('/start', methods=['POST'])
def start_simulator():
    """启动BLE设备模拟器"""
    logger.info("启动BLE设备模拟器")

    try:
        # 如果未初始化，先初始化
        if not ble_peripheral_service.is_initialized:
            success = ble_peripheral_service.initialize()
            if not success:
                flash("BLE外围设备服务初始化失败", 'error')
                return redirect(url_for('peripheral.simulator'))

        # 启动外围设备
        result = ble_peripheral_service.start_peripheral()

        if result["success"]:
            flash(result["message"], 'success')
        else:
            flash(result["message"], 'error')

    except Exception as e:
        logger.error(f"启动BLE设备模拟器失败: {str(e)}")
        flash(f"启动失败: {str(e)}", 'error')

    return redirect(url_for('peripheral.simulator'))


@peripheral_bp.route('/stop', methods=['POST'])
def stop_simulator():
    """停止BLE设备模拟器"""
    logger.info("停止BLE设备模拟器")

    try:
        result = ble_peripheral_service.stop_peripheral()

        if result["success"]:
            flash(result["message"], 'success')
        else:
            flash(result["message"], 'error')

    except Exception as e:
        logger.error(f"停止BLE设备模拟器失败: {str(e)}")
        flash(f"停止失败: {str(e)}", 'error')

    return redirect(url_for('peripheral.simulator'))


@peripheral_bp.route('/set_data', methods=['POST'])
def set_grip_data():
    """设置握力数据"""
    logger.info("设置握力数据")

    try:
        data = request.form.get('data', '').strip()
        if not data:
            flash("请输入握力数据", 'warning')
            return redirect(url_for('peripheral.simulator'))

        result = ble_peripheral_service.set_grip_data(data)

        if result["success"]:
            flash(f"握力数据设置成功: {data}", 'success')
        else:
            flash(result["message"], 'error')

    except Exception as e:
        logger.error(f"设置握力数据失败: {str(e)}")
        flash(f"设置失败: {str(e)}", 'error')

    return redirect(url_for('peripheral.simulator'))


@peripheral_bp.route('/set_mode', methods=['POST'])
def set_simulation_mode():
    """设置模拟模式"""
    logger.info("设置模拟模式")

    try:
        mode = request.form.get('mode', '').strip()
        if mode not in ['normal', 'exercise', 'rest']:
            flash("无效的模拟模式", 'warning')
            return redirect(url_for('peripheral.simulator'))

        result = ble_peripheral_service.set_simulation_mode(mode)

        if result["success"]:
            flash(result["message"], 'success')
        else:
            flash(result["message"], 'error')

    except Exception as e:
        logger.error(f"设置模拟模式失败: {str(e)}")
        flash(f"设置失败: {str(e)}", 'error')

    return redirect(url_for('peripheral.simulator'))


@peripheral_bp.route('/api/status')
def api_get_status():
    """API: 获取状态"""
    try:
        status = ble_peripheral_service.get_status()
        return jsonify({
            "success": True,
            "data": status
        })
    except Exception as e:
        logger.error(f"获取状态失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@peripheral_bp.route('/api/data/current')
def api_get_current_data():
    """API: 获取当前数据"""
    try:
        current_data = ble_peripheral_service.get_current_grip_data()
        return jsonify({
            "success": True,
            "data": current_data
        })
    except Exception as e:
        logger.error(f"获取当前数据失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@peripheral_bp.route('/api/history')
def api_get_history():
    """API: 获取历史数据"""
    try:
        limit = request.args.get('limit', 50, type=int)
        if limit <= 0 or limit > 1000:
            limit = 50

        history = ble_peripheral_service.get_data_history(limit)
        return jsonify({
            "success": True,
            "data": history
        })
    except Exception as e:
        logger.error(f"获取历史数据失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500