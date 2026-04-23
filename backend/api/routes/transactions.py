"""Transaction history endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, delete
from ...db.database import get_db
from ...db.models import Transaction
from ...blockchain.nanopayments import NanopaymentsClient

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.get("")
async def get_transactions(limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Transaction).order_by(desc(Transaction.created_at)).limit(limit)
    )
    txns = result.scalars().all()
    return {
        "transactions": [
            {
                "id": str(t.id),
                "from_agent": t.from_agent,
                "to_agent": t.to_agent,
                "amount_usdc": float(t.amount_usdc),
                "tx_hash": t.tx_hash,
                "task_type": t.task_type,
                "status": t.status,
                "timestamp": t.created_at.isoformat() if t.created_at else None,
            }
            for t in txns
        ],
        "total": len(txns),
    }


@router.delete("/clear")
async def clear_transactions(db: AsyncSession = Depends(get_db)):
    """Delete all transactions — fresh start for demo."""
    await db.execute(delete(Transaction))
    await db.commit()
    return {"cleared": True, "message": "All transactions deleted"}


@router.get("/margin-analysis")
async def margin_analysis():
    """Economic proof: why sub-cent pricing fails on gas-based chains."""
    client = NanopaymentsClient()
    return {
        "data_analyst": client.margin_analysis(0.003, 1000),
        "content_writer": client.margin_analysis(0.005, 1000),
        "code_reviewer": client.margin_analysis(0.008, 1000),
        "translator": client.margin_analysis(0.002, 1000),
        "summary": (
            "At $0.003/task: gas-based chains lose $997/1000 txns. "
            "Arc Nanopayments: profit $2.999/1000 txns. "
            "Arc enables 99.9999% cost reduction vs traditional gas."
        ),
    }
