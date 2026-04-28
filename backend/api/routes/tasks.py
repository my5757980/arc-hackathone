"""Task execution endpoint — main entry point for agent tasks with wallet balance tracking."""
import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...blockchain.x402 import build_x402_header, verify_x402_payment, x402_payment_response
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
    gemini_function_calls: list = []


class ChainTaskRequest(BaseModel):
    input: str
    payer_wallet_id: str = "demo-wallet"
    payer_address: str = "0x0000000000000000000000000000000000000000"


@router.post("", response_model=TaskResponse)
async def execute_task(request: TaskRequest, db: AsyncSession = Depends(get_db)):
    from ...main import orchestrator, broadcast_transaction
    try:
        task_result = await orchestrator.process_task(
            task_type=request.task_type,
            task_input=request.input,
            payer_wallet_id=request.payer_wallet_id,
            payer_address=request.payer_address,
        )
        task_id = str(uuid.uuid4())
        now = datetime.utcnow()

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

        result = await db.execute(
            select(AgentWallet).where(AgentWallet.agent_name == task_result.agent)
        )
        agent_wallet = result.scalar_one_or_none()
        if agent_wallet:
            agent_wallet.balance_usdc = float(agent_wallet.balance_usdc) + task_result.cost_usdc

        await db.commit()

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
            gemini_function_calls=task_result.function_calls or [],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/x402")
async def x402_payment_gate():
    """x402 HTTP 402 Payment Required — agent services require USDC payment on Arc."""
    orchestrator_address = os.getenv(
        "ORCHESTRATOR_WALLET_ADDRESS",
        "0x1919ed21ea0c7c56e2a89eb998333395fda5c81e",
    )
    return await x402_payment_response(
        payee_address=orchestrator_address,
        amount_usdc=0.003,
        service="AgentFlow-DataAnalyst",
    )


@router.post("/x402-execute", response_model=TaskResponse)
async def x402_execute_task(
    request: TaskRequest,
    x_payment: Optional[str] = Header(None, alias="X-Payment"),
    db: AsyncSession = Depends(get_db),
):
    """
    x402 HTTP payment protocol endpoint.
    - No X-Payment header → returns 402 with payment requirements.
    - Valid X-Payment header → verifies USDC payment, executes agent task.
    Agent-to-agent callers use this to autonomously pay and consume services.
    """
    min_amount = 0.003
    orchestrator_address = os.getenv(
        "ORCHESTRATOR_WALLET_ADDRESS",
        "0x1919ed21ea0c7c56e2a89eb998333395fda5c81e",
    )

    if not x_payment or not verify_x402_payment(x_payment, min_amount):
        return await x402_payment_response(
            payee_address=orchestrator_address,
            amount_usdc=min_amount,
            service=request.task_type,
        )

    # Payment verified — execute task
    return await execute_task(request, db)


@router.post("/chain")
async def execute_chain_task(request: ChainTaskRequest, db: AsyncSession = Depends(get_db)):
    """
    Agent-to-agent payment chain:
      User → pays DataAnalyst → DataAnalyst pays ContentWriter → final report.
    Two real Circle DCW transactions on Arc. Proves peer-to-peer agent economy.
    """
    from ...main import orchestrator, broadcast_transaction
    try:
        chain_result = await orchestrator.chain_task(
            task_input=request.input,
            payer_wallet_id=request.payer_wallet_id,
            payer_address=request.payer_address,
        )

        now = datetime.utcnow()
        for step in chain_result["chain"]:
            tx = Transaction(
                from_agent=step["payer"],
                to_agent=step["payee"],
                amount_usdc=step["amount_usdc"],
                tx_hash=step["tx_hash"],
                task_type="agent-chain",
                task_input=request.input[:200],
                task_result=step["result"][:500],
                status="confirmed",
                created_at=now,
            )
            db.add(tx)
            await broadcast_transaction({
                "from_agent": step["payer"],
                "to_agent": step["payee"],
                "amount_usdc": step["amount_usdc"],
                "tx_hash": step["tx_hash"],
                "task_type": "agent-to-agent-chain",
                "task_result": step["result"][:200],
                "timestamp": now.isoformat(),
                "status": "confirmed",
            })

        await db.commit()
        return chain_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
