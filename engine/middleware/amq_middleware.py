from typing import Any, Dict, Optional
import aio_pika
from .base_middleware import BaseMiddleware


class AMQMiddleware(BaseMiddleware):
    def __init__(self, url: str, queue_name: str, channel_name: str, queue_config: Optional[Dict[str, Any]] = None):
        """
        Initialize AMQ middleware with connection parameters
        
        Args:
            url (str): The URL of the message broker
            queue_name (str): Name of the queue to connect to
            channel_name (str): Name of the channel to use (for logging purposes only)
            queue_config (Dict[str, Any], optional): Queue configuration parameters
        """
        super().__init__()
        self.url = url
        self.queue_name = queue_name
        self.channel_name = channel_name
        self.queue_config = queue_config or {}
        self.connection = None
        self.channel = None
        self.queue = None

    async def connect(self) -> None:
        """Establish connection to the message broker"""
        self.connection = await aio_pika.connect_robust(self.url)
        # Use None to let aio_pika automatically assign a channel number
        self.channel = await self.connection.channel()

        # Declare exchange
        exchange = await self.channel.declare_exchange(
            "amphibia_exchange",
            aio_pika.ExchangeType.DIRECT,
            durable=True
        )

        # Declare queue with configuration
        self.queue = await self.channel.declare_queue(
            self.queue_name,
            **self.queue_config
        )

        # Bind queue to exchange with queue name as routing key
        await self.queue.bind(
            exchange,
            routing_key=self.queue_name
        )

    async def disconnect(self) -> None:
        """Close connection to the message broker"""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            self.connection = None
            self.channel = None
            self.queue = None
