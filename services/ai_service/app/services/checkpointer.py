from langgraph.checkpoint.postgres import PostgresSaver
from app.core.config import settings

checkpointer = PostgresSaver.from_conn_string(settings.AI_DATABASE_URl)