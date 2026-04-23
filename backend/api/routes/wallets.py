"""Agent wallet endpoints — live Circle API balances with DB fallback."""
import os

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...blockchain.circle_wallets import CircleWalletsClient
from ...db.database import get_db
from ...db.models import AgentWallet

router = APIRouter(prefix="/api/wallets", tags=["wallets"])

WALLET_IDS = {
    "Orchestrator":  os.getenv("ORCHESTRATOR_WALLET_ID",   "8137508b-a29f-5795-ad11-f1e08aa0bedd"),
    "DataAnalyst":   os.getenv("DATA_ANALYST_WALLET_ID",   "76bd15c1-d9c6-58c4-ab78-b8323bd66e15"),
    "ContentWriter": os.getenv("CONTENT_WRITER_WALLET_ID", "32493bbc-b42a-56ef-a9dd-cc3ea7b8b0da"),
    "CodeReviewer":  os.getenv("CODE_REVIEWER_WALLET_ID",  "12e692a6-f5be-5740-910b-2415a9b245fd"),
    "Translator":    os.getenv("TRANSLATOR_WALLET_ID",     "b44632f8-f56b-57d4-a1c6-7e224e69474d"),
}


@router.get("")
async def get_wallets(db: AsyncSession = Depends(get_db)):
    """Return agent wallet info with live Circle balances where available."""
    result = await db.execute(select(AgentWallet))
    db_wallets = {w.agent_name: w for w in result.scalars().all()}

    circle_client = CircleWalletsClient()
    wallets_out = []

    for agent_name, wallet_id in WALLET_IDS.items():
        if agent_name == "Orchestrator":
            continue  # Orchestrator is internal, skip from display

        db_w = db_wallets.get(agent_name)

        # Try live Circle balance
        live_balance = await circle_client.get_balance(wallet_id)
        balance = live_balance if live_balance > 0 else (float(db_w.balance_usdc) if db_w else 20.0)

        # Update DB if live balance differs
        if db_w and live_balance > 0:
            db_w.balance_usdc = live_balance

        wallets_out.append({
            "agent_name": agent_name,
            "wallet_address": db_w.wallet_address if db_w else "",
            "circle_wallet_id": wallet_id,
            "balance_usdc": balance,
            "balance_source": "live" if live_balance > 0 else "cached",
        })

    try:
        await db.commit()
    except Exception:
        await db.rollback()

    return {"wallets": wallets_out}
