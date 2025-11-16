from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base


# noinspection PyTypeChecker
class PostgresDataSource:
    def __init__(self, username, password, host, port, db_name, base=None, ssl=False):
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.db_name = db_name
        self.ssl = ssl
        self.base = base or declarative_base()  # Default to declarative_base if base is not provided
        self.engine = None
        self.session = None

    async def connect(self):
        try:
            database_url = f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.db_name}"

            # Configure connect_args based on ssl setting
            connect_args = {}
            if not self.ssl:
                connect_args["ssl"] = False

            self.engine = create_async_engine(
                database_url,
                echo=False,
                connect_args=connect_args,
                # Connection pool settings to prevent connection leaks
                pool_size=10,  # Maximum number of connections to maintain in the pool
                max_overflow=20,  # Maximum number of connections that can be created beyond pool_size
                pool_timeout=30,  # Seconds to wait before giving up on getting a connection from the pool
                pool_recycle=3600,  # Recycle connections after 1 hour to prevent stale connections
                pool_pre_ping=True,  # Verify connections before using them
            )
            
            self.base.metadata.bind = self.engine  # Bind the engine to the Base metadata

            self.session = sessionmaker(
                bind=self.engine, 
                expire_on_commit=False, 
                class_=AsyncSession
            )
            
        except SQLAlchemyError as e:
            self.engine = None
            self.session = None
            raise Exception(f"Database connection error: {e}")

    async def get_session(self):
        if self.engine is None or self.session is None:
            await self.connect()
        return self.session()

    async def close(self):
        if self.engine:
            await self.engine.dispose()
