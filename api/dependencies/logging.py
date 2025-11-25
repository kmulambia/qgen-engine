import logging
from engine.utils.logger_util import get_logger
from engine.utils.config_util import load_config

config = load_config()

MODE = config.get_variable("MODE", "development")
# Set log level based on MODE: DEBUG for development, INFO for production
log_level = logging.DEBUG if MODE == "development" else logging.INFO
logger = get_logger("api_logger", log_path="logs/api.log", level=log_level, sqlalchemy_log_level=logging.CRITICAL)
