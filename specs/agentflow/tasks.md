# Tasks: AgentFlow
# Version: 1.0.0 | Stage: tasks | 2026-04-21

## Phase 1 — Blockchain Infrastructure
- [x] T01: Create .env.example with all Circle + Gemini + Neon keys
- [x] T02: Implement CircleWalletsClient (create wallet, get balance, list wallets)
- [x] T03: Implement NanopaymentsClient (initiate payment, verify payment, get status)
- [x] T04: Implement ArcClient (web3 connection, tx confirmation, balance check)
- [x] T05: Implement X402Middleware (parse 402 header, attach payment, verify)
- [x] T06: Create agent_wallets DB table + seed 5 agent wallets on startup

## Phase 2 — AI Agents
- [x] T07: BaseAgent abstract class (execute, get_price, get_wallet)
- [x] T08: OrchestratorAgent (route task, charge routing fee, coordinate payment)
- [x] T09: DataAnalystAgent (Gemini Flash, analyze data/CSV, $0.003)
- [x] T10: ContentWriterAgent (Gemini Flash, write content, $0.005)
- [x] T11: CodeReviewerAgent (Gemini Flash, review code, $0.008)
- [x] T12: TranslatorAgent (Gemini Flash, translate text, $0.002)

## Phase 3 — FastAPI Backend
- [x] T13: POST /api/tasks endpoint (orchestrator entry point)
- [x] T14: GET /api/transactions endpoint (transaction history)
- [x] T15: GET /api/wallets endpoint (agent wallet balances)
- [x] T16: POST /api/demo/run endpoint (trigger 50+ auto transactions)
- [x] T17: GET /api/events SSE endpoint (real-time transaction stream)
- [x] T18: Database models + migrations (SQLAlchemy + asyncpg)

## Phase 4 — Next.js Dashboard
- [x] T19: Layout + dark neon theme (globals.css)
- [x] T20: Dashboard hero (title, stats: total txns, total USDC, agents active)
- [x] T21: TransactionFeed component (SSE stream, live rows, tx hash links)
- [x] T22: AgentCard components (name, balance, tasks completed, price/task)
- [x] T23: MarginCalculator component (gas vs Nanopayments cost comparison)
- [x] T24: DemoButton component (trigger 50 txns, progress bar)

## Phase 5 — Demo + Deploy
- [x] T25: demo_runner.py script (50 automated tasks, varied agents)
- [x] T26: docker-compose.yml (backend + frontend + postgres local)
- [x] T27: Railway deployment config (Procfile + railway.json)
- [x] T28: Vercel deployment config (vercel.json + env vars)
- [x] T29: README.md (setup guide + economic analysis + demo instructions)
- [x] T30: PHR for full build

## Test Cases
- TC-01: DataAnalyst task returns result + tx_hash in <2s
- TC-02: Insufficient balance returns 402 with payment instructions
- TC-03: 50 demo transactions complete in <60s
- TC-04: Dashboard shows all 50 transactions within 500ms each
- TC-05: Agent wallet balances change correctly after each transaction
