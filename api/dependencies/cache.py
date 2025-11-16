from engine.datasources.redis_ds import RedisDS
from engine.utils.config_util import load_config

config = load_config()

cache = RedisDS(
    host=config.require_variable("REDIS_HOST"),
    port=config.require_variable("REDIS_PORT", int),
    password=config.require_variable("REDIS_PASSWORD"),
    db=config.require_variable("REDIS_DB", int)
)


async def get_cache():
    await cache.connect()
    return cache
