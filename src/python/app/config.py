"""Application Configuration"""
import os
from pathlib import Path
from typing import Optional

class Config:
    """Base configuration class"""

    def __init__(self):
        # 项目根目录
        self.PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

        # Flask 配置
        self.SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
        self.FLASK_APP = 'app.main:flask_app'
        self.FLASK_ENV = os.environ.get('FLASK_ENV') or 'development'

        # FastAPI 配置
        self.API_V1_STR = "/api/v1"
        self.PROJECT_NAME = "BLE Simulator API"
        self.PROJECT_VERSION = "1.0.0"

        # 服务器配置
        self.HOST = os.environ.get('HOST') or '0.0.0.0'
        self.PORT = int(os.environ.get('PORT') or 18080)
        self.DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

        # 日志配置
        self.LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'

        # 模板和静态文件路径
        self.TEMPLATE_FOLDER = str(self.PROJECT_ROOT / "src" / "python" / "templates")
        self.STATIC_FOLDER = str(self.PROJECT_ROOT / "src" / "python" / "static")

class DevelopmentConfig(Config):
    """Development configuration"""

    def __init__(self):
        super().__init__()
        self.DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""

    def __init__(self):
        super().__init__()
        self.DEBUG = False
        self.SECRET_KEY = os.environ.get('SECRET_KEY')
        if not self.SECRET_KEY:
            raise ValueError("SECRET_KEY environment variable must be set in production")

class TestingConfig(Config):
    """Testing configuration"""

    def __init__(self):
        super().__init__()
        self.TESTING = True
        self.DEBUG = True

# 配置映射
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name: Optional[str] = None) -> Config:
    """获取配置对象"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    return config_map.get(config_name, DevelopmentConfig)()