import logging
from engine.utils.logger_util import get_logger
from engine.utils.config_util import load_config

config = load_config()

MODE = config.get_variable("MODE", "development")
logger = get_logger("mailer_logger", log_path="logs/mailer.log", sqlalchemy_log_level=logging.INFO)

logger.setLevel(logging.INFO)
