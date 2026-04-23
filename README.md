# AgentFlow — Autonomous AI Agent Economy on Arc

**Hackathon:** Agentic Economy on Arc | April 20–26, 2026
**Track:** Agent-to-Agent Payment Loop
**Prize Pool:** $15,000+
**Team:** Muhammad Yaseen

> The first autonomous AI agent marketplace where machines pay each other in real-time, per-task, using Circle Nanopayments on Arc EVM L1 — without gas overhead eroding margin.

---

## What It Does

AgentFlow is an autonomous AI agent economy:

- **4 Specialized AI Agents** powered by Gemini 2.5 Flash: DataAnalyst, ContentWriter, CodeReviewer, Translator
- **Real-time USDC micropayments** via Circle Developer Controlled Wallets on Arc EVM L1
- **Sub-cent pricing**: $0.002–$0.008 USDC per task (economically impossible on gas-based chains)
- **Orchestrator** routes tasks + collects $0.001 USDC routing fee per request
- **Live dashboard** with SSE real-time transaction feed
- **Demo mode**: 55 autonomous Circle DCW transfers in ~30 seconds

---

## Economic Proof (Hackathon Required)

| Metric | Gas-Based (ETH) | Arc Nanopayments |
|---|---|---|
| Cost per transaction | ~$1.00 | ~$0.000001 |
| Revenue per task | $0.003 USDC | $0.003 USDC |
| Net on 1000 txns | **-$997 LOSS** | **+$2.999 PROFIT** |
| Economically viable? | **NO** | **YES** |

**Conclusion:** Arc Nanopayments reduce overhead by 99.9999% — enabling sub-cent AI agent commerce that is impossible on any gas-based chain.

**API:** `GET /api/transactions/margin-analysis` returns full per-agent economic breakdown.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Blockchain | Arc EVM L1 (Circle) — ARC-TESTNET, Chain ID 60000 |
| Stablecoin | USDC (native gas token on Arc) |
| Payments | Circle Nanopayments API + Circle Dev Controlled Wallets |
| Wallets | 5 Circle Developer Controlled Wallets (funded 20 USDC each) |
| Protocol | x402 HTTP Payment Standard |
| AI | Gemini 2.5 Flash Preview (`gemini-2.5-flash-preview-04-17`) |
| Backend | Python 3.11 + FastAPI + uv |
| Frontend | Next.js 15 + Tailwind CSS (dark neon UI) |
| Database | Neon PostgreSQL (serverless) |
| Deploy | Railway (backend) + Vercel (frontend) |

---

## Agent Pricing

| Agent | Task | Price (USDC) |
|---|---|---|
| DataAnalyst | Data analysis + insights | $0.003 |
| ContentWriter | Content generation | $0.005 |
| CodeReviewer | Code review + security | $0.008 |
| Translator | Text translation | $0.002 |
| Orchestrator | Routing fee | $0.001 |

---

## Setup & Run

### Prerequisites
- Python 3.11+, Node.js 20+, uv
- Circle Developer Account (credentials in `.env`)
- Gemini API key

### Quick Start (Docker)
```bash
git clone <repo-url>
cd agentflow
cp .env.example .env  # fill in keys
docker compose up
# Browser: http://localhost:3000
```

### Manual Start
```bash
# Terminal 1 — Backend (MUST run from project root, NOT from backend/)
uv --directory backend sync
backend/.venv/Scripts/python.exe -m uvicorn backend.main:app --reload --port 8000
# On Linux/Mac: backend/.venv/bin/python -m uvicorn backend.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev

# Browser: http://localhost:3000
# Click "🗑 Clear All Data" first → then "▶ Run Demo (55 txns)" → watch live transactions
```

### Run Demo from CLI
```bash
python3 demo_runner.py
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | /api/tasks | Execute agent task + pay USDC |
| GET | /api/transactions | Full transaction history |
| GET | /api/transactions/margin-analysis | Economic proof (gas vs Arc) |
| GET | /api/wallets | Live agent wallet balances |
| POST | /api/demo/run | Trigger 55 Circle DCW transfers |
| GET | /api/events | SSE real-time transaction stream |
| GET | /health | Health check |

---

## Project Structure

```
agentflow/
├── backend/
│   ├── main.py                    — FastAPI app + SSE broadcast
│   ├── agents/
│   │   ├── base_agent.py          — Gemini 2.5 Flash base class
│   │   ├── orchestrator.py        — Task routing + payment flow
│   │   ├── data_analyst.py        — $0.003/task
│   │   ├── content_writer.py      — $0.005/task
│   │   ├── code_reviewer.py       — $0.008/task
│   │   └── translator.py          — $0.002/task
│   ├── blockchain/
│   │   ├── nanopayments.py        — Circle Nanopayments client
│   │   ├── circle_wallets.py      — DCW + entity secret RSA signing
│   │   └── x402.py                — x402 HTTP payment protocol
│   ├── api/routes/
│   │   ├── tasks.py               — POST /api/tasks
│   │   ├── transactions.py        — GET /api/transactions
│   │   ├── wallets.py             — GET /api/wallets (live Circle balance)
│   │   └── demo.py                — POST /api/demo/run
│   └── db/
│       ├── models.py              — Transaction + AgentWallet models
│       └── database.py            — Neon PostgreSQL async
├── frontend/
│   └── app/page.tsx               — Next.js 15 dark neon dashboard
├── demo_runner.py                 — CLI demo (55 transactions)
├── docker-compose.yml
└── Procfile                       — Railway deploy
```

---

## Circle Integration Notes

- **Circle API Key:** `TEST_API_KEY:...` (developer account)
- **Entity Secret:** Used for RSA-OAEP signing of Developer Controlled Wallet transactions
- **Wallet Set:** 5 wallets on ARC-TESTNET, each funded with 20 USDC via testnet faucet
- **Nanopayments:** Code correctly calls `/v1/nanopayments/payments`. Arc testnet endpoint returns 404 (infrastructure not yet stable). Falls back to Circle DCW transfer automatically — real Arc onchain transactions still generated.
- **x402 Protocol:** Fully implemented for agent-to-agent HTTP payment negotiation
- **Arc EVM:** Chain ID 60000, RPC `https://rpc.arc.circle.com/testnet`
- **Gas format (Arc-specific):** Top-level `gasLimit=100000, priorityFee=1, maxFee=25` — NOT the nested `fee.config.feeLevel` format (Circle docs show generic EVM format; Arc testnet requires EIP-1559 style top-level fields)

---

## Verify Transactions On-Chain

- **Arc Testnet Explorer (Blockscout):** https://testnet.arcscan.app
- **Circle Console:** https://console.circle.com (Wallet Set → Transactions)
- All tx hashes in the live feed link directly to `testnet.arcscan.app/tx/<hash>`

---

## Deploy

**Backend (Railway):**
```bash
railway login && railway init && railway up
```

**Frontend (Vercel):**
```bash
vercel --cwd frontend
# Set NEXT_PUBLIC_API_URL to Railway backend URL in Vercel dashboard
```

---

Built for **Agentic Economy on Arc** Hackathon 2026
Circle Nanopayments + Arc EVM L1 + Gemini 2.5 Flash + Circle Developer Controlled Wallets
