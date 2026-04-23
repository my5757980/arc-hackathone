"""Circle Developer Controlled Wallets — real Arc onchain transfers via entity secret."""
import asyncio
import base64
import hashlib
import os
import uuid

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

CIRCLE_API_KEY = os.getenv("CIRCLE_API_KEY", "")
CIRCLE_ENTITY_SECRET = os.getenv("CIRCLE_ENTITY_SECRET", "")
CIRCLE_BASE_URL = "https://api.circle.com/v1/w3s"

_public_key_cache: str | None = None


async def _fetch_circle_public_key() -> str:
    global _public_key_cache
    if _public_key_cache:
        return _public_key_cache
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{CIRCLE_BASE_URL}/config/entity/publicKey",
            headers={"Authorization": f"Bearer {CIRCLE_API_KEY}"},
        )
        resp.raise_for_status()
        _public_key_cache = resp.json()["data"]["publicKey"]
    return _public_key_cache


def _encrypt_entity_secret(public_key_pem: str, entity_secret_hex: str) -> str:
    """RSA-OAEP-SHA256 encrypt entity secret for Circle DCW API."""
    public_key = serialization.load_pem_public_key(public_key_pem.encode())
    secret_bytes = bytes.fromhex(entity_secret_hex)
    encrypted = public_key.encrypt(
        secret_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return base64.b64encode(encrypted).decode()


class CircleWalletsClient:
    def __init__(self):
        self.api_key = CIRCLE_API_KEY
        self.entity_secret = CIRCLE_ENTITY_SECRET
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def _entity_ciphertext(self) -> str:
        pub_key = await _fetch_circle_public_key()
        return _encrypt_entity_secret(pub_key, self.entity_secret)

    async def transfer(
        self,
        source_wallet_id: str,
        dest_address: str,
        amount_usdc: float,
        idempotency_key: str,
    ) -> dict:
        """Transfer USDC via Circle Developer Controlled Wallets → real Arc onchain tx."""
        entity_ciphertext = await self._entity_ciphertext()
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{CIRCLE_BASE_URL}/developer/transactions/transfer",
                headers=self.headers,
                json={
                    "idempotencyKey": idempotency_key,
                    "entitySecretCiphertext": entity_ciphertext,
                    "walletId": source_wallet_id,
                    "tokenId": os.getenv("ARC_USDC_TOKEN_ID", ""),
                    "amounts": [f"{amount_usdc:.6f}"],
                    "destinationAddress": dest_address,
                    "gasLimit": "100000",
                    "priorityFee": "1",
                    "maxFee": "25",
                },
            )
            if not resp.is_success:
                raise ValueError(
                    f"Circle DCW transfer failed: {resp.status_code} — {resp.text[:300]}"
                )
            tx_id = resp.json()["data"]["id"]

        # Poll up to 20s for onchain confirmation + real tx hash
        tx_hash = await self._poll_tx_hash(tx_id, max_wait=20)
        return {
            "id": tx_id,
            "txHash": tx_hash or f"arc-pending-{tx_id[:8]}",
            "state": "CONFIRMED" if tx_hash else "PENDING",
            "amount_usdc": amount_usdc,
        }

    async def _poll_tx_hash(self, tx_id: str, max_wait: int = 20) -> str | None:
        """Poll Circle API until Arc tx hash is available."""
        async with httpx.AsyncClient(timeout=10) as client:
            for _ in range(max_wait // 2):
                await asyncio.sleep(2)
                try:
                    r = await client.get(
                        f"{CIRCLE_BASE_URL}/transactions/{tx_id}",
                        headers=self.headers,
                    )
                    if r.is_success:
                        tx = r.json()["data"]["transaction"]
                        if tx.get("txHash"):
                            return tx["txHash"]
                except Exception:
                    pass
        return None

    async def get_balance(self, wallet_id: str) -> float:
        """Get live USDC balance from Circle API."""
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                resp = await client.get(
                    f"{CIRCLE_BASE_URL}/wallets/{wallet_id}/balances",
                    headers=self.headers,
                )
                if resp.is_success:
                    for bal in resp.json()["data"]["tokenBalances"]:
                        if bal["token"]["symbol"] == "USDC":
                            return float(bal["amount"])
            except Exception:
                pass
        return 0.0

    async def transfer_immediate(
        self,
        source_wallet_id: str,
        dest_address: str,
        amount_usdc: float,
        idempotency_key: str,
    ) -> dict:
        """Fire Circle DCW transfer and return immediately — NO polling. Fast for demos."""
        entity_ciphertext = await self._entity_ciphertext()
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{CIRCLE_BASE_URL}/developer/transactions/transfer",
                headers=self.headers,
                json={
                    "idempotencyKey": idempotency_key,
                    "entitySecretCiphertext": entity_ciphertext,
                    "walletId": source_wallet_id,
                    "tokenId": os.getenv("ARC_USDC_TOKEN_ID", ""),
                    "amounts": [f"{amount_usdc:.6f}"],
                    "destinationAddress": dest_address,
                    "gasLimit": "100000",
                    "priorityFee": "1",
                    "maxFee": "25",
                },
            )
            if not resp.is_success:
                raise ValueError(
                    f"Circle DCW transfer failed: {resp.status_code} — {resp.text[:200]}"
                )
            tx_id = resp.json()["data"]["id"]
            # Return Circle transaction ID immediately — tx hash resolves onchain later
            return {
                "id": tx_id,
                "txHash": f"arc-{tx_id.replace('-', '')[:32]}",
                "state": "INITIATED",
                "amount_usdc": amount_usdc,
            }

    async def transfer_with_fallback(
        self,
        source_wallet_id: str,
        dest_address: str,
        amount_usdc: float,
        idempotency_key: str,
        memo: str = "",
    ) -> dict:
        """Try real DCW transfer (immediate); fall back to simulation on any failure."""
        try:
            return await self.transfer_immediate(
                source_wallet_id, dest_address, amount_usdc, idempotency_key
            )
        except Exception as e:
            fake_hash = "0x" + hashlib.sha256(
                f"{idempotency_key}{dest_address}{amount_usdc}".encode()
            ).hexdigest()
            return {
                "id": idempotency_key,
                "txHash": fake_hash,
                "state": "simulated",
                "amount_usdc": amount_usdc,
                "error": str(e)[:100],
            }
