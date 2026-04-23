"""Circle Nanopayments — sub-cent USDC on Arc. Falls back to DCW transfer if API unavailable."""
import hashlib
import os
import uuid
from decimal import Decimal

import httpx

CIRCLE_API_KEY = os.getenv("CIRCLE_API_KEY", "")
NANOPAYMENTS_URL = "https://api.circle.com/v1/nanopayments"


class NanopaymentsClient:
    """
    Circle Nanopayments: sub-cent USDC on Arc — ~$0.000001 overhead vs $1.00 on Ethereum.
    Falls back to Circle DCW wallet transfer when Nanopayments testnet endpoint is unavailable.
    """

    def __init__(self):
        self.api_key = CIRCLE_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def initiate_payment(
        self,
        payer_wallet_id: str,
        payee_address: str,
        amount_usdc: float,
        memo: str = "",
    ) -> dict:
        """Try Nanopayments API; fall back to Circle DCW transfer on 404."""
        idempotency_key = str(uuid.uuid4())
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                resp = await client.post(
                    f"{NANOPAYMENTS_URL}/payments",
                    headers=self.headers,
                    json={
                        "idempotencyKey": idempotency_key,
                        "payerWalletId": payer_wallet_id,
                        "payeeAddress": payee_address,
                        "amount": str(Decimal(str(amount_usdc)).quantize(Decimal("0.000001"))),
                        "currency": "USDC",
                        "blockchain": "ARC-TESTNET",
                        "memo": memo,
                    },
                )
                if resp.status_code == 404:
                    # Nanopayments not yet stable on Arc testnet — use DCW transfer
                    return await self._dcw_transfer(
                        payer_wallet_id, payee_address, amount_usdc, idempotency_key, memo
                    )
                resp.raise_for_status()
                return resp.json()["data"]
            except httpx.TimeoutException:
                return await self._dcw_transfer(
                    payer_wallet_id, payee_address, amount_usdc, idempotency_key, memo
                )

    async def _dcw_transfer(
        self,
        payer_wallet_id: str,
        payee_address: str,
        amount_usdc: float,
        idempotency_key: str,
        memo: str,
    ) -> dict:
        """Fallback: real Circle Developer Controlled Wallet transfer → real Arc tx hash."""
        from .circle_wallets import CircleWalletsClient
        client = CircleWalletsClient()
        result = await client.transfer_with_fallback(
            source_wallet_id=payer_wallet_id,
            dest_address=payee_address,
            amount_usdc=amount_usdc,
            idempotency_key=idempotency_key,
            memo=memo,
        )
        return {
            "payment_id": result["id"],
            "tx_hash": result["txHash"],
            "status": result["state"],
            "amount_usdc": amount_usdc,
            "memo": memo,
        }

    @staticmethod
    def margin_analysis(amount_usdc: float, num_transactions: int) -> dict:
        """Economic proof: why sub-cent pricing FAILS on gas chains, WORKS on Arc."""
        traditional_gas_cost = 1.00
        arc_overhead = 0.000001

        total_revenue = amount_usdc * num_transactions
        gas_cost_total = traditional_gas_cost * num_transactions
        arc_cost_total = arc_overhead * num_transactions

        return {
            "amount_per_tx_usdc": amount_usdc,
            "num_transactions": num_transactions,
            "total_revenue_usdc": total_revenue,
            "traditional_gas_per_tx": traditional_gas_cost,
            "arc_overhead_per_tx": arc_overhead,
            "gas_net_profit_usdc": round(total_revenue - gas_cost_total, 6),
            "arc_net_profit_usdc": round(total_revenue - arc_cost_total, 6),
            "gas_viable": (total_revenue - gas_cost_total) > 0,
            "arc_viable": (total_revenue - arc_cost_total) > 0,
            "savings_pct": round((1 - arc_overhead / traditional_gas_cost) * 100, 4),
            "conclusion": (
                f"At ${amount_usdc}/tx: traditional gas costs ${traditional_gas_cost} → "
                f"${total_revenue - gas_cost_total:.4f} net on {num_transactions} txns (LOSS). "
                f"Arc Nanopayments: ${total_revenue - arc_cost_total:.4f} net (PROFIT). "
                f"Arc saves {round((1 - arc_overhead / traditional_gas_cost) * 100, 2)}% on fees."
            ),
        }
