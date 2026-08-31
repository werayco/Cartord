from enum import Enum
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class AIRequest(BaseModel):
    query: str

class Conversation(BaseModel):
    user_id: UUID