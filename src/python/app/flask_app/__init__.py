"""Flask Application Module"""
from flask import Flask
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.python.utils.log_util import LogUtil
from .routes import main_bp
from .blueprints.ble_bp import ble_bp

logger = LogUtil.get_logger('flask_app')

def create_flask_app(config):
    """Flask应用工厂函数"""
    logger.info("创建Flask应用实例")

    app = Flask(
        __name__,
        template_folder=config.TEMPLATE_FOLDER,
        static_folder=config.STATIC_FOLDER
    )

    # 配置应用
    app.config.from_object(config)

    # 注册蓝图
    app.register_blueprint(main_bp)
    app.register_blueprint(ble_bp)

    logger.info(f"Flask应用创建完成，模板目录: {config.TEMPLATE_FOLDER}")
    logger.info(f"静态文件目录: {config.STATIC_FOLDER}")

    return app