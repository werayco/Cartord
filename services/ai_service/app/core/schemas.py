from enum import Enum
from pydantic import BaseModel, ConfigDict

class AIRequest(BaseModel):
    query: str
