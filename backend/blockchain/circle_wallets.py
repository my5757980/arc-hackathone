"""Circle Programmable Wallets API client."""
import httpx
import os
from typing import Optional

CIRCLE_API_KEY = os.getenv("CIRCLE_API_KEY", "")
CIRCLE_BASE_URL = "https://api.circle.com/v1/w3s"


class CircleWalletsClient:
    def __init__(self):
        self.api_key = CIRCLE_API_KEY
        self.base_url = CIRCLE_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def create_wallet(self, agent_name: str, blockchain: str = "ARC-TESTNET") -> dict:
        """Create a new Circle-managed wallet for an agent."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/wallets",
                headers=self.headers,
                json={
                    "idempotencyKey": f"agentflow-{agent_name}-{blockchain}",
                    "blockchains": [blockchain],
                    "metadata": [{"name": agent_name, "refId": agent_name}],
                },
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()["data"]["wallets"][0]

    async def get_balance(self, wallet_id: str) -> float:
        """Get USDC balance for a wallet."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/wallets/{wallet_id}/balances",
                headers=self.headers,
                timeout=10,
            )
            resp.raise_for_status()
            balances = resp.json()["data"]["tokenBalances"]
            for bal in balances:
                if bal["token"]["symbol"] == "USDC":
                    return float(bal["amount"])
            return 0.0

    async def transfer(
        self,
        source_wallet_id: str,
        dest_address: str,
        amount_usdc: float,
        idempotency_key: str,
    ) -> dict:
        """Transfer USDC from one wallet to another."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/transactions/transfer",
                headers=self.headers,
                json={
                    "idempotencyKey": idempotency_key,
                    "walletId": source_wallet_id,
                    "tokenId": os.getenv("ARC_USDC_TOKEN_ID", ""),
                    "amounts": [str(amount_usdc)],
                    "destinationAddress": dest_address,
                    "fee": {"type": "level", "config": {"feeLevel": "MEDIUM"}},
                },
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()["data"]["transfer"]

    async def get_transaction(self, tx_id: str) -> dict:
        """Get transaction status."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/transactions/{tx_id}",
                headers=self.headers,
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()["data"]["transaction"]
