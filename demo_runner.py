"""
AgentFlow Demo Runner
Fires 55 autonomous agent transactions on Arc testnet.
Run: python3 demo_runner.py
"""
import asyncio
import httpx
import random
import time

API = "http://localhost:8000"

TASKS = [
    ("analyze", "Q1 2026 revenue: $1.2M, 340 customers, 89% retention, NPS 72"),
    ("write",   "Write a tagline for an AI micropayment platform on Arc blockchain"),
    ("review",  "def transfer(to, amt): wallet.send(to, amt); log(amt)"),
    ("translate", "La econom\u00eda agentiva es el futuro del comercio digital"),
    ("analyze", "DAU 12k, MAU 45k, avg session 4.2min, D7 retention 61%"),
    ("write",   "Subject line: developer hackathon for AI + USDC micropayments"),
    ("review",  "async function pay(addr, usdc) { return await circle.transfer(addr, usdc) }"),
    ("translate", "Arc ist die L1-Blockchain fuer stablecoin-native Zahlungen"),
    ("analyze", "API calls: 50k/day, p99 latency 340ms, error rate 0.3%"),
    ("write",   "One-liner description of sub-cent AI agent commerce"),
]


async def run_demo(count: int = 55):
    print(f"AgentFlow Demo — firing {count} autonomous transactions on Arc testnet")
    print("=" * 60)
    start = time.time()
    success = 0
    total_usdc = 0.0

    async with httpx.AsyncClient(timeout=30) as client:
        for i in range(count):
            task_type, task_input = random.choice(TASKS)
            try:
                resp = await client.post(f"{API}/api/tasks", json={
                    "task_type": task_type,
                    "input": task_input,
                    "payer_wallet_id": "demo-wallet",
                    "payer_address": "0x0000000000000000000000000000000000000000",
                })
                if resp.status_code == 200:
                    data = resp.json()
                    success += 1
                    total_usdc += data["cost_usdc"]
                    print(f"[{i+1:03d}] {data['agent']:15s} | ${data['cost_usdc']:.4f} USDC | {data['tx_hash'][:16]}... | {task_type}")
                else:
                    print(f"[{i+1:03d}] ERROR {resp.status_code}")
            except Exception as e:
                print(f"[{i+1:03d}] EXCEPTION: {e}")
            await asyncio.sleep(0.3)

    elapsed = time.time() - start
    print("=" * 60)
    print(f"COMPLETE: {success}/{count} transactions | ${total_usdc:.4f} USDC | {elapsed:.1f}s")
    print(f"Visit http://localhost:3000 to see the live dashboard")


if __name__ == "__main__":
    asyncio.run(run_demo())
