"""Demo runner — triggers 50+ autonomous agent transactions."""
import asyncio
import random
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ...db.database import get_db

router = APIRouter(prefix="/api/demo", tags=["demo"])

DEMO_TASKS = [
    ("analyze", "Q1 2026 sales: $1.2M revenue, 340 customers, 89% retention rate"),
    ("write", "Write a tagline for an AI agent payment platform"),
    ("review", "def pay(amount): balance -= amount; return True"),
    ("translate", "La economía agentiva es el futuro de las transacciones digitales"),
    ("analyze", "User metrics: DAU 12k, MAU 45k, avg session 4.2min, churn 3%"),
    ("write", "Product description for sub-cent USDC micropayments on Arc blockchain"),
    ("review", "async function transfer(to, amount) { await wallet.send(to, amount) }"),
    ("translate", "Arc est la blockchain L1 native pour les paiements stablecoin"),
    ("analyze", "Token price: $0.003 per API call, 50k calls/day, 99.7% uptime"),
    ("write", "Email subject line for developer hackathon announcement"),
]


async def run_demo_transactions(count: int, db):
    from ...main import orchestrator, broadcast_transaction
    import uuid
    from datetime import datetime
    from ...db.models import Transaction

    async with db as session:
        for i in range(count):
            task_type, task_input = random.choice(DEMO_TASKS)
            try:
                result = await orchestrator.process_task(
                    task_type=task_type,
                    task_input=task_input,
                    payer_wallet_id="demo-wallet",
                    payer_address="0x0000000000000000000000000000000000000000",
                )
                now = datetime.utcnow()
                tx = Transaction(
                    from_agent="DemoUser",
                    to_agent=result.agent,
                    amount_usdc=result.cost_usdc,
                    tx_hash=result.tx_hash,
                    task_type=task_type,
                    task_input=task_input[:200],
                    task_result=result.result[:500],
                    status="confirmed",
                    created_at=now,
                )
                session.add(tx)
                await session.commit()
                await broadcast_transaction({
                    "id": str(tx.id),
                    "from_agent": "DemoUser",
                    "to_agent": result.agent,
                    "amount_usdc": result.cost_usdc,
                    "tx_hash": result.tx_hash,
                    "task_type": task_type,
                    "timestamp": now.isoformat(),
                    "status": "confirmed",
                })
            except Exception:
                pass
            await asyncio.sleep(0.5)  # 0.5s between txns = 100 txns in 50s


@router.post("/run")
async def run_demo(
    background_tasks: BackgroundTasks,
    count: int = 55,
):
    from ...db.database import AsyncSessionLocal
    background_tasks.add_task(
        run_demo_transactions, count, AsyncSessionLocal()
    )
    return {
        "started": True,
        "transaction_count": count,
        "estimated_seconds": count * 0.5,
        "message": f"Running {count} autonomous agent transactions on Arc testnet...",
    }
