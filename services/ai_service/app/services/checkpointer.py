from langgraph.checkpoint.postgres import PostgresSaver
from app.core.config import settings
from app.core.logging import logger

async def get_checkpointer():
    logger.info("connecting to checkpointer")
    checkpointer = None
    try:
        checkpointer = PostgresSaver.from_conn_string(settings.AI_DATABASE_URL)
        await checkpointer.setup()
        logger.info("checkpointer connected successfully")
        yield checkpointer
    finally:
        if checkpointer:
            await checkpointer.close()