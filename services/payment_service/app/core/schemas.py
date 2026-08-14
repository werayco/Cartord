from pydantic import BaseModel
import uuid

class WalletCreate(BaseModel):
    user_id: uuid.UUID