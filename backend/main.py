"""
AgentFlow — Autonomous AI Agent Economy
FastAPI backend with Circle Nanopayments + Arc EVM L1 + Gemini Flash
"""
import asyncio
import json
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .db.database import init_db, AsyncSessionLocal
from .db.models import AgentWallet
from .agents.orchestrator import OrchestratorAgent
from .agents.data_analyst import DataAnalystAgent
from .agents.content_writer import ContentWriterAgent
from .agents.code_reviewer import CodeReviewerAgent
from .agents.translator import TranslatorAgent

# SSE broadcast queue
_sse_queues: list[asyncio.Queue] = []

# Global orchestrator
orchestrator: OrchestratorAgent = None


async def broadcast_transaction(tx_data: dict):
    """Broadcast transaction to all SSE clients."""
    message = f"data: {json.dumps(tx_data)}\n\n"
    for queue in _sse_queues:
        await queue.put(message)


async def seed_agent_wallets(session):
    """Seed demo agent wallets if not present."""
    from sqlalchemy import select
    result = await session.execute(select(AgentWallet))
    existing = result.scalars().all()
    if existing:
        return

    demo_wallets = [
        AgentWallet(agent_name="Orchestrator", circle_wallet_id="demo-orchestrator", wallet_address="0x1111111111111111111111111111111111111111", balance_usdc=100.0),
        AgentWallet(agent_name="DataAnalyst",  circle_wallet_id="demo-data-analyst", wallet_address="0x2222222222222222222222222222222222222222", balance_usdc=50.0),
        AgentWallet(agent_name="ContentWriter",circle_wallet_id="demo-content-writer",wallet_address="0x3333333333333333333333333333333333333333", balance_usdc=50.0),
        AgentWallet(agent_name="CodeReviewer", circle_wallet_id="demo-code-reviewer", wallet_address="0x4444444444444444444444444444444444444444", balance_usdc=50.0),
        AgentWallet(agent_name="Translator",   circle_wallet_id="demo-translator",    wallet_address="0x5555555555555555555555555555555555555555", balance_usdc=50.0),
    ]
    for w in demo_wallets:
        session.add(w)
    await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global orchestrator
    # Init DB
    await init_db()
    async with AsyncSessionLocal() as session:
        await seed_agent_wallets(session)
        # Load wallet addresses
        from sqlalchemy import select
        result = await session.execute(select(AgentWallet))
        wallets = {w.agent_name: w for w in result.scalars().all()}

    # Build agents
    agents = {
        "DataAnalyst":   DataAnalystAgent(wallet_address=wallets.get("DataAnalyst", AgentWallet(wallet_address="0x2222222222222222222222222222222222222222")).wallet_address),
        "ContentWriter": ContentWriterAgent(wallet_address=wallets.get("ContentWriter", AgentWallet(wallet_address="0x3333333333333333333333333333333333333333")).wallet_address),
        "CodeReviewer":  CodeReviewerAgent(wallet_address=wallets.get("CodeReviewer", AgentWallet(wallet_address="0x4444444444444444444444444444444444444444")).wallet_address),
        "Translator":    TranslatorAgent(wallet_address=wallets.get("Translator", AgentWallet(wallet_address="0x5555555555555555555555555555555555555555")).wallet_address),
    }
    orchestrator = OrchestratorAgent()
    orchestrator.register_agents(agents)
    os.environ.setdefault("ORCHESTRATOR_WALLET_ADDRESS", "0x1111111111111111111111111111111111111111")
    yield


app = FastAPI(
    title="AgentFlow — Autonomous AI Agent Economy",
    description="Sub-cent USDC micropayments between AI agents via Arc Nanopayments",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
from .api.routes import tasks, transactions, wallets, demo
app.include_router(tasks.router)
app.include_router(transactions.router)
app.include_router(wallets.router)
app.include_router(demo.router)


@app.get("/")
async def root():
    return {
        "name": "AgentFlow",
        "tagline": "Autonomous AI Agent Economy on Arc",
        "version": "1.0.0",
        "hackathon": "Agentic Economy on Arc — April 2026",
        "track": "Agent-to-Agent Payment Loop",
        "agents": ["DataAnalyst", "ContentWriter", "CodeReviewer", "Translator"],
        "pricing": {"DataAnalyst": "$0.003", "ContentWriter": "$0.005", "CodeReviewer": "$0.008", "Translator": "$0.002"},
    }


@app.get("/api/events")
async def events():
    """SSE endpoint for real-time transaction stream."""
    queue: asyncio.Queue = asyncio.Queue()
    _sse_queues.append(queue)

    async def generate() -> AsyncGenerator[str, None]:
        try:
            yield "data: {\"type\": \"connected\", \"message\": \"AgentFlow SSE stream\"}\n\n"
            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=30)
                    yield message
                except asyncio.TimeoutError:
                    yield "data: {\"type\": \"heartbeat\"}\n\n"
        finally:
            _sse_queues.remove(queue)

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "agentflow-backend"}
