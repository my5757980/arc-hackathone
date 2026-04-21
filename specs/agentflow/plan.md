# Architecture Plan: AgentFlow
# Version: 1.0.0 | Stage: plan | 2026-04-21

## System Architecture

```
User/Demo Script
     |
     v
[FastAPI Orchestrator] -- x402 Payment --> [Circle Nanopayments]
     |                                            |
     |-- routes task -->                    [Arc EVM L1]
     |                                            |
[Specialized Agents]  <-- USDC settle ---  [Circle Wallets API]
  - DataAnalyst
  - ContentWriter
  - CodeReviewer
  - Translator
     |
     v
[Gemini Flash AI] --> result
     |
     v
[Neon PostgreSQL] -- transaction log
     |
     v
[Next.js Dashboard] -- real-time SSE feed
```

## Key Architecture Decisions

### AD-01: x402 for HTTP-Native Payments
x402 embeds payment verification in HTTP headers (402 Payment Required).
Agents call each other's REST endpoints. If payment header missing → 402 response.
On payment included → 200 + result. No separate payment step.
Rationale: cleanest agent-to-agent UX, industry-standard emerging protocol.

### AD-02: Circle Programmable Wallets (not self-custody)
Each agent gets a Circle-managed wallet at startup. Private keys never exposed.
Rationale: faster demo setup, Circle hackathon infrastructure, no key management complexity.

### AD-03: Gemini Flash for Agent Intelligence
gemini-2.0-flash: lowest latency (<500ms), optimized for transactional agents.
Rationale: matches hackathon recommendation, free tier sufficient for demo.

### AD-04: Server-Sent Events for Dashboard
FastAPI /events endpoint streams transactions to Next.js dashboard in real-time.
Rationale: no WebSocket complexity, works through Railway proxy, simple client code.

### AD-05: Demo Script = 50+ transactions in 60 seconds
Automated Python script calls Orchestrator 50 times with varied tasks.
Rationale: meets hackathon judging criteria deterministically.

## API Contract

### POST /api/tasks
Request: { task_type: str, input: str, budget_usdc: float }
Response: { task_id: str, result: str, tx_hash: str, cost_usdc: float, agent: str }
Errors: 402 (insufficient balance), 400 (invalid task), 503 (agent unavailable)

### GET /api/transactions
Response: { transactions: [{ id, from_agent, to_agent, amount_usdc, tx_hash, timestamp, task_type }] }

### GET /api/wallets
Response: { wallets: [{ agent_name, address, balance_usdc }] }

### POST /api/demo/run
Response: { started: true, transaction_count: int, estimated_seconds: int }

### GET /api/events (SSE)
Stream: data: { type: "transaction", payload: {...} }

## Database Schema (Neon PostgreSQL)

```sql
CREATE TABLE transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  from_agent VARCHAR(50) NOT NULL,
  to_agent VARCHAR(50) NOT NULL,
  amount_usdc DECIMAL(18,8) NOT NULL,
  tx_hash VARCHAR(66),
  arc_block_number BIGINT,
  task_type VARCHAR(50),
  task_input TEXT,
  task_result TEXT,
  status VARCHAR(20) DEFAULT 'pending',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE agent_wallets (
  agent_name VARCHAR(50) PRIMARY KEY,
  circle_wallet_id VARCHAR(100) UNIQUE NOT NULL,
  wallet_address VARCHAR(42) NOT NULL,
  balance_usdc DECIMAL(18,8) DEFAULT 0
);
```

## NFRs
- p95 latency per task: <2000ms (AI call dominates)
- Transaction throughput: 10+ tx/second (Arc Nanopayments handles burst)
- Demo script: 50 transactions in <60 seconds
- Dashboard update: <500ms after onchain confirmation

## Deployment
- Backend: Railway (Python FastAPI, PORT=8000)
- Frontend: Vercel (Next.js 15, points to Railway backend)
- Database: Neon PostgreSQL (serverless, free tier)
- Arc: Testnet (Arc Sepolia equivalent)
