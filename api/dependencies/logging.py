import logging
from engine.utils.logger_util import get_logger
from engine.utils.config_util import load_config

config = load_config()

MODE = config.get_variable("MODE", "development")
# TODO: if MODE is production, set log level to INFO else set to DEBUG
logger = get_logger("api_logger", log_path="logs/api.log", sqlalchemy_log_level=logging.CRITICAL)
