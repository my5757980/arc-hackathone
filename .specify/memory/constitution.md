# AgentFlow Constitution
# Version: 1.0.0 | 2026-04-21 | Muhammad Yaseen

## Project Identity
AgentFlow is an autonomous AI agent marketplace where specialized agents pay each other
per-task in real-time USDC via Arc Nanopayments. Sub-cent machine-to-machine commerce.

## Hackathon Context
- Event: Agentic Economy on Arc | April 20-26, 2026
- Track: Agent-to-Agent Payment Loop
- Prize Pool: $15,000+
- Required: Arc EVM L1, USDC, Circle Nanopayments, sub-cent (<=0.01 USDC) transactions

## Core Principles
P1 - Sub-Cent First: every agent task <= $0.01 USDC, no batching, real-time settlement
P2 - Economic Proof: 50+ onchain txns + margin explanation vs gas-based chains
P3 - Autonomous Agents: no human approval for agent-to-agent payments
P4 - Circle-Native Stack: Circle Wallets + Nanopayments + x402 protocol
P5 - No Hardcoded Secrets: all keys via .env, never committed
P6 - SDD Pipeline: Constitution -> Specify -> Plan -> Tasks -> Implement -> PHR

## Tech Stack (LOCKED)
Backend: Python 3.11+ + FastAPI + uv
AI: Gemini Flash (gemini-2.0-flash) + OpenAI Agent SDK
Blockchain: Arc EVM L1, USDC, Circle Nanopayments API, x402
Wallets: Circle Programmable Wallets API
Database: Neon PostgreSQL (serverless)
Frontend: Next.js 15 + Tailwind CSS (dark neon theme)
Deploy: Railway (backend) + Vercel (frontend)

## Agent Pricing
DataAnalyst:   $0.003 USDC per task
ContentWriter: $0.005 USDC per task
CodeReviewer:  $0.008 USDC per task
Translator:    $0.002 USDC per task
Orchestrator:  $0.001 USDC routing fee
