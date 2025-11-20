import json
import aio_pika
from typing import Dict, Any
from engine.utils.config_util import load_config
from engine.middleware.amq_middleware import AMQMiddleware
from api.dependencies.logging import logger

config = load_config()

# Queue configuration
QUEUE_CONFIG = {
    "durable": True,
    "auto_delete": False
}


async def send_email_message(message: Dict[str, Any]) -> bool | None:
    """
    Send an email message to the message queue.
    
    Args:
        message (Dict[str, Any]): The message to send, containing email details
        
    Returns:
        bool: True if a message was sent successfully, False otherwise
    """
    success = False  # noqa
    try:
        # Get queue name with default
        queue_name = config.get_variable("AMQ_QUEUE_NAME", "engine")
        channel_name = config.get_variable("AMQ_EMAIL_SERVICE", "email")
        
        # Get AMQ URI, construct from RABBITMQ_* vars if not provided
        amq_uri = config.get_variable("AMQ_URI")
        if not amq_uri:
            # Construct from RABBITMQ configuration
            rabbitmq_host = config.get_variable("RABBITMQ_HOST", "localhost")
            rabbitmq_port = config.get_variable("RABBITMQ_PORT", "5672")
            rabbitmq_user = config.get_variable("RABBITMQ_DEFAULT_USER", "guest")
            rabbitmq_pass = config.get_variable("RABBITMQ_DEFAULT_PASS", "guest")
            amq_uri = f"amqp://{rabbitmq_user}:{rabbitmq_pass}@{rabbitmq_host}:{rabbitmq_port}/"
        
        logger.info(f"Attempting to send email message to queue: {queue_name}")

        # Create AMQ middleware instance
        amq = AMQMiddleware(
            url=amq_uri,
            queue_name=queue_name,
            channel_name=channel_name,
            queue_config=QUEUE_CONFIG
        )

        # Connect to RabbitMQ
        await amq.connect()

        try:
            # Prepare a message
            message_body = json.dumps(message)
            message = aio_pika.Message(
                body=message_body.encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )

            # Get the exchange we declared in connect()
            exchange = await amq.channel.get_exchange("amphibia_exchange")

            # Send a message using the exchange
            await exchange.publish(
                message,
                routing_key=queue_name
            )

            logger.info(f"Successfully sent email message to queue: {queue_name}")
            return True
        except Exception as e:
            logger.error(f"Error sending email message: {str(e)}", exc_info=True)
            return False
        # finally:
        #     # Always disconnect
        #     await amq.disconnect()
        #     return False

    except Exception as e:
        logger.error(f"Error sending email message: {str(e)}", exc_info=True)
        success = False

    return success
