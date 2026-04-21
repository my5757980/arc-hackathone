"""Agent wallet endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...db.database import get_db
from ...db.models import AgentWallet

router = APIRouter(prefix="/api/wallets", tags=["wallets"])


@router.get("")
async def get_wallets(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AgentWallet))
    wallets = result.scalars().all()
    return {
        "wallets": [
            {
                "agent_name": w.agent_name,
                "wallet_address": w.wallet_address,
                "balance_usdc": float(w.balance_usdc),
            }
            for w in wallets
        ]
    }
