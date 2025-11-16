import oracledb
from contextlib import asynccontextmanager
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OracleDataSource:
    def __init__(
            self,
            host: str,
            port: int,
            service_name: Optional[str] = None,
            sid: Optional[str] = None,
            user: Optional[str] = None,
            password: Optional[str] = None,
            min_size: int = 2,
            max_size: int = 5,
            increment: int = 1,
            timeout: int = 7200,  # 2 hours in seconds
            max_retries: int = 3
    ):
        self.host = host
        self.port = port
        self.service_name = service_name
        self.sid = sid
        self.user = user
        self.password = password
        self.min_size = min_size
        self.max_size = max_size
        self.increment = increment
        self.timeout = timeout
        self.max_retries = max_retries
        self.pool = None

    async def connect(self):
        """Create the connection pool"""
        if not self.pool:  # Only create pool if it doesn't exist
            if self.sid:
                dsn = f"{self.host}:{self.port}:{self.sid}"
            else:
                dsn = f"{self.host}:{self.port}/{self.service_name}"

            try:
                self.pool = oracledb.create_pool(
                    user=self.user,
                    password=self.password,
                    dsn=dsn,
                    min=self.min_size,
                    max=self.max_size,
                    increment=self.increment,
                    getmode=oracledb.POOL_GETMODE_WAIT,
                    wait_timeout=60,
                    timeout=self.timeout,
                    retry_count=self.max_retries,
                    retry_delay=2,
                    ping_interval=60
                )
                logger.info(f"Connection pool created successfully. Size: {self.min_size}-{self.max_size}")

            except Exception as e:
                logger.error(f"Error creating connection pool: {e}")
                raise

        return self

    @asynccontextmanager
    async def cursor_context(self):
        """Context manager for database cursors"""
        if not self.pool:
            await self.connect()

        conn = None
        cursor = None
        try:
            conn = self.pool.acquire()
            cursor = conn.cursor()
            yield cursor
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.pool.release(conn)

    async def close(self):
        """Close the connection pool"""
        if self.pool:
            self.pool.close()
            self.pool = None
