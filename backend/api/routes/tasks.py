"""Task execution endpoint — main entry point for agent tasks."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert
import uuid
from datetime import datetime

from ...db.database import get_db
from ...db.models import Transaction
from ...agents.orchestrator import OrchestratorAgent

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

        # Save to DB
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
        await db.commit()

        # Broadcast to SSE
        from ...main import broadcast_transaction
        await broadcast_transaction({
            "id": str(tx.id),
            "from_agent": "User",
            "to_agent": task_result.agent,
            "amount_usdc": task_result.cost_usdc,
            "tx_hash": task_result.tx_hash,
            "task_type": request.task_type,
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
