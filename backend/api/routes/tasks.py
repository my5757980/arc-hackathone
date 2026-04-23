"""Task execution endpoint — main entry point for agent tasks with wallet balance tracking."""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.database import get_db
from ...db.models import AgentWallet, Transaction

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


class TaskRequest(BaseModel):
    task_type: str  # analyze | write | review | translate
    input: str
    payer_wallet_id: str = "demo-wallet"
    payer_address: str = "0x0000000000000000000000000000000000000000"


class TaskResponse(BaseModel):
    task_id: str
    agent: str
    result: str
    cost_usdc: float
    tx_hash: str
    task_type: str
    timestamp: str


@router.post("", response_model=TaskResponse)
async def execute_task(request: TaskRequest, db: AsyncSession = Depends(get_db)):
    from ...main import orchestrator
    try:
        task_result = await orchestrator.process_task(
            task_type=request.task_type,
            task_input=request.input,
            payer_wallet_id=request.payer_wallet_id,
            payer_address=request.payer_address,
        )
        task_id = str(uuid.uuid4())
        now = datetime.utcnow()

        # Save transaction to DB
        tx = Transaction(
            from_agent="User",
            to_agent=task_result.agent,
            amount_usdc=task_result.cost_usdc,
            tx_hash=task_result.tx_hash,
            task_type=request.task_type,
            task_input=request.input[:500],
            task_result=task_result.result[:1000],
            status="confirmed",
            created_at=now,
        )
        db.add(tx)

        # Update agent wallet balance in DB (deduct cost from agent's tracked balance)
        result = await db.execute(
            select(AgentWallet).where(AgentWallet.agent_name == task_result.agent)
        )
        agent_wallet = result.scalar_one_or_none()
        if agent_wallet:
            # Agent earns the task price (receives USDC)
            agent_wallet.balance_usdc = float(agent_wallet.balance_usdc) + task_result.cost_usdc

        await db.commit()

        # Broadcast to SSE live feed
        from ...main import broadcast_transaction
        await broadcast_transaction({
            "id": str(tx.id),
            "from_agent": "User",
            "to_agent": task_result.agent,
            "amount_usdc": task_result.cost_usdc,
            "tx_hash": task_result.tx_hash,
            "task_type": request.task_type,
            "task_result": task_result.result[:200],
            "timestamp": now.isoformat(),
            "status": "confirmed",
        })

        return TaskResponse(
            task_id=task_id,
            agent=task_result.agent,
            result=task_result.result,
            cost_usdc=task_result.cost_usdc,
            tx_hash=task_result.tx_hash,
            task_type=request.task_type,
            timestamp=now.isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
