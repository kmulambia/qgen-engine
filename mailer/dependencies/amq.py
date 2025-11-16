from engine.middleware.amq_middleware import AMQMiddleware
from engine.utils.config_util import load_config
from mailer.dependencies.logger import logger

config = load_config()

# AMQ Configuration
AMQ_URI = config.require_variable("AMQ_URI")
AMQ_QUEUE_NAME = config.require_variable("AMQ_QUEUE_NAME")
AMQ_EMAIL_SERVICE = config.require_variable("AMQ_EMAIL_SERVICE")

# Create a single instance to be reused
_amq_middleware = None


async def get_amq() -> AMQMiddleware:
    """Get AMQ middleware instance."""
    global _amq_middleware

    try:
        if _amq_middleware is None:
            _amq_middleware = AMQMiddleware(
                url=AMQ_URI,
                queue_name=AMQ_QUEUE_NAME,
                channel_name=AMQ_EMAIL_SERVICE,
                queue_config={
                    "durable": True,
                    "auto_delete": False
                }
            )
            await _amq_middleware.connect()

        return _amq_middleware
    except Exception as e:
        logger.error(f"Error connecting to AMQ broker: {e}")
        raise
