# AgentFlow — Autonomous AI Agent Economy on Arc

**Hackathon:** Agentic Economy on Arc | April 20-26, 2026
**Track:** Agent-to-Agent Payment Loop
**Prize Pool:** $15,000+

> Sub-cent USDC micropayments between AI agents via Circle Nanopayments on Arc EVM L1.
> The first agent marketplace where machines pay each other in real-time, per-task, without gas overhead.

---

## What It Does

AgentFlow is an autonomous AI agent marketplace:

- **4 Specialized Agents**: DataAnalyst, ContentWriter, CodeReviewer, Translator
- **Real-time USDC payments**: Each agent task triggers a Circle Nanopayment on Arc
- **Sub-cent pricing**: $0.002–$0.008 USDC per task (impossible on gas-based chains)
- **Live dashboard**: Real-time feed of all agent-to-agent transactions
- **Demo mode**: 55 autonomous transactions in 30 seconds

---

## Economic Proof (Required by Hackathon)

| Metric              | Gas-Based (ETH)    | Arc Nanopayments   |
|---------------------|--------------------|--------------------|
| Cost per transaction | ~$1.00            | ~$0.000001         |
| Revenue per task     | $0.003 USDC       | $0.003 USDC        |
| Net profit (1000 tx) | **-$997 LOSS**    | **+$2.999 PROFIT** |
| Economically viable? | NO                | YES                |

**Conclusion:** Arc Nanopayments reduce transaction overhead by 99.9999%, making sub-cent AI agent commerce viable for the first time.

---

## Tech Stack

| Component     | Technology                              |
|---------------|-----------------------------------------|
| Blockchain    | Arc EVM L1 (Circle)                     |
| Stablecoin    | USDC                                    |
| Payments      | Circle Nanopayments API                 |
| Wallets       | Circle Programmable Wallets             |
| Protocol      | x402 HTTP Payment Standard             |
| AI            | Gemini Flash (gemini-2.5-flash)               |
| Backend       | Python 3.11 + FastAPI + uv              |
| Frontend      | Next.js 15 + Tailwind CSS               |
| Database      | Neon PostgreSQL (serverless)            |
| Deploy        | Railway (backend) + Vercel (frontend)   |

---

## Setup

### 1. Prerequisites
- Python 3.11+, Node.js 20+, uv
- Circle Developer Account (free)
- Gemini API key (free tier)
- Neon PostgreSQL (free tier)

### 2. Clone & Configure
```bash
git clone https://github.com/yourusername/agentflow
cd agentflow
cp .env.example .env
# Fill in your Circle API key, Gemini API key, Neon DB URL
```

### 3. Run with Docker
```bash
docker compose up
```

### 4. Run Manually
```bash
# Backend
cd backend
uv sync
uv run uvicorn backend.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### 5. Run Demo (55 Transactions)
```bash
python3 demo_runner.py
```
Or click **"Run Demo"** button in the dashboard at http://localhost:3000

---

## API Endpoints

| Method | Endpoint              | Description                      |
|--------|-----------------------|----------------------------------|
| POST   | /api/tasks            | Execute agent task + pay         |
| GET    | /api/transactions     | Transaction history              |
| GET    | /api/wallets          | Agent wallet balances            |
| POST   | /api/demo/run         | Trigger 55 auto-transactions     |
| GET    | /api/events           | SSE real-time transaction stream |
| GET    | /api/transactions/margin-analysis | Economic proof data |

---

## Agent Pricing

| Agent         | Task                  | Price (USDC) |
|---------------|-----------------------|--------------|
| DataAnalyst   | Data analysis         | $0.003       |
| ContentWriter | Content generation    | $0.005       |
| CodeReviewer  | Code review           | $0.008       |
| Translator    | Text translation      | $0.002       |
| Orchestrator  | Routing fee           | $0.001       |

---

## Deploy

**Backend (Railway):**
```bash
railway login
railway init
railway up
```

**Frontend (Vercel):**
```bash
vercel --cwd frontend
```

Set `NEXT_PUBLIC_API_URL` to your Railway backend URL in Vercel env vars.

---

Built with Circle Nanopayments + Arc EVM L1 + Gemini Flash
Agentic Economy on Arc Hackathon 2026
