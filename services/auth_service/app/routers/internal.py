from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.schemas import DelegateRequest
from app.core.logging import logger
from app.core.utils import DELEGATED_TOKEN_EXPIRE_SECONDS, issue_delegated_token, authenticate_ai_agent, AI_AGENT_SCOPES
from app.db.session import get_db
from app.models.buyer import Buyer

internal_router = APIRouter(prefix="/internal/v1", tags=["internal"])

@internal_router.post("/token/delegate")
async def delegate_token(body: DelegateRequest,actor: str = Depends(authenticate_ai_agent),db: AsyncSession = Depends(get_db)):
    if not set(body.scopes) <= AI_AGENT_SCOPES:
        logger.warning(f"delegation refused: actor={actor} user={body.user_id} scopes={body.scopes}")
        raise HTTPException(status_code=403, detail="Scope not allowed for this service")

    result = await db.execute(select(Buyer).where(Buyer.id == body.user_id))
    buyer = result.scalar_one_or_none()
    if buyer is None:
        raise HTTPException(status_code=404, detail="User not found")

    logger.info(f"delegated token: actor={actor} user={buyer.id} scopes={body.scopes}")
    return {
        "access_token": issue_delegated_token(buyer, body.scopes, actor),
        "expires_in": DELEGATED_TOKEN_EXPIRE_SECONDS,
    }
