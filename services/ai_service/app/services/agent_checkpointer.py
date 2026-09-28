from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
from app.core.config import settings
from app.core.logging import logger

pool: AsyncConnectionPool | None = None
checkpointer: AsyncPostgresSaver | None = None

async def get_checkpointer() -> AsyncPostgresSaver:
    global pool, checkpointer
    if checkpointer is not None:
        return checkpointer
    
    dsn = settings.AI_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://", 1)
    pool = AsyncConnectionPool(conninfo=dsn,max_size=20,kwargs={"autocommit": True, "prepare_threshold": 0},open=False,)

    await pool.open()

    checkpointer = AsyncPostgresSaver(pool)
    await checkpointer.setup()

    checkpointer = checkpointer
    logger.info("checkpointer connected successfully")
    return checkpointer