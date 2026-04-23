"""
AgentFlow — Autonomous AI Agent Economy on Arc
FastAPI backend: Circle Nanopayments + Circle DCW + Arc EVM L1 + Gemini 2.5 Flash
"""
import asyncio
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

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
        AgentWallet(agent_name="Orchestrator", circle_wallet_id=os.getenv("ORCHESTRATOR_WALLET_ID", "8137508b-a29f-5795-ad11-f1e08aa0bedd"), wallet_address=os.getenv("ORCHESTRATOR_WALLET_ADDRESS", "0x1919ed21ea0c7c56e2a89eb998333395fda5c81e"), balance_usdc=100.0),
        AgentWallet(agent_name="DataAnalyst",  circle_wallet_id=os.getenv("DATA_ANALYST_WALLET_ID",  "76bd15c1-d9c6-58c4-ab78-b8323bd66e15"), wallet_address=os.getenv("DATA_ANALYST_WALLET_ADDRESS",  "0x059ac920d925896cf8b08f9fe9eeae1b7ac625d7"), balance_usdc=50.0),
        AgentWallet(agent_name="ContentWriter",circle_wallet_id=os.getenv("CONTENT_WRITER_WALLET_ID","32493bbc-b42a-56ef-a9dd-cc3ea7b8b0da"), wallet_address=os.getenv("CONTENT_WRITER_WALLET_ADDRESS","0xf66ec96a7c0ca6a6736ccbc989b6226a9cde43f7"), balance_usdc=50.0),
        AgentWallet(agent_name="CodeReviewer", circle_wallet_id=os.getenv("CODE_REVIEWER_WALLET_ID", "12e692a6-f5be-5740-910b-2415a9b245fd"), wallet_address=os.getenv("CODE_REVIEWER_WALLET_ADDRESS", "0x7b022ac63b55b42ee388e2341205f3215098b7f2"), balance_usdc=50.0),
        AgentWallet(agent_name="Translator",   circle_wallet_id=os.getenv("TRANSLATOR_WALLET_ID",    "b44632f8-f56b-57d4-a1c6-7e224e69474d"), wallet_address=os.getenv("TRANSLATOR_WALLET_ADDRESS",    "0x0f1d54b006fa65b1d3afbbac65f2d9dc816b9bbf"), balance_usdc=50.0),
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
        "DataAnalyst":   DataAnalystAgent(wallet_address=wallets.get("DataAnalyst", AgentWallet(wallet_address=os.getenv("DATA_ANALYST_WALLET_ADDRESS", "0x059ac920d925896cf8b08f9fe9eeae1b7ac625d7"))).wallet_address),
        "ContentWriter": ContentWriterAgent(wallet_address=wallets.get("ContentWriter", AgentWallet(wallet_address=os.getenv("CONTENT_WRITER_WALLET_ADDRESS", "0xf66ec96a7c0ca6a6736ccbc989b6226a9cde43f7"))).wallet_address),
        "CodeReviewer":  CodeReviewerAgent(wallet_address=wallets.get("CodeReviewer", AgentWallet(wallet_address=os.getenv("CODE_REVIEWER_WALLET_ADDRESS", "0x7b022ac63b55b42ee388e2341205f3215098b7f2"))).wallet_address),
        "Translator":    TranslatorAgent(wallet_address=wallets.get("Translator", AgentWallet(wallet_address=os.getenv("TRANSLATOR_WALLET_ADDRESS", "0x0f1d54b006fa65b1d3afbbac65f2d9dc816b9bbf"))).wallet_address),
    }
    orchestrator = OrchestratorAgent()
    orchestrator.register_agents(agents)
    os.environ.setdefault("ORCHESTRATOR_WALLET_ADDRESS", os.getenv("ORCHESTRATOR_WALLET_ADDRESS", "0x1919ed21ea0c7c56e2a89eb998333395fda5c81e"))
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
