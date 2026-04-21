"""x402 HTTP payment protocol middleware for agent-to-agent payments."""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import base64
import json
import os


class X402PaymentRequired(Exception):
    def __init__(self, payee_address: str, amount_usdc: float, service: str):
        self.payee_address = payee_address
        self.amount_usdc = amount_usdc
        self.service = service


def build_x402_header(payee_address: str, amount_usdc: float, service: str) -> dict:
    """Build x402 Payment-Required response headers."""
    payment_details = {
        "scheme": "exact",
        "network": "arc-testnet",
        "maxAmountRequired": str(int(amount_usdc * 1_000_000)),  # USDC has 6 decimals
        "resource": service,
        "description": f"AgentFlow: {service} service",
        "mimeType": "application/json",
        "payTo": payee_address,
        "maxTimeoutSeconds": 60,
        "asset": os.getenv("ARC_USDC_CONTRACT", "0x0000000000000000000000000000000000000001"),
        "extra": {"version": "1.0", "scheme": "exact"},
    }
    encoded = base64.b64encode(json.dumps(payment_details).encode()).decode()
    return {
        "X-Payment-Required": encoded,
        "Accept-Payment-Scheme": "exact",
    }


def verify_x402_payment(payment_header: str, expected_amount: float) -> bool:
    """Verify an incoming x402 payment header."""
    if not payment_header:
        return False
    try:
        decoded = base64.b64decode(payment_header).decode()
        payment = json.loads(decoded)
        amount = int(payment.get("amount", 0)) / 1_000_000
        return amount >= expected_amount
    except Exception:
        return False


async def x402_payment_response(payee_address: str, amount_usdc: float, service: str):
    """Return a 402 Payment Required response."""
    headers = build_x402_header(payee_address, amount_usdc, service)
    return JSONResponse(
        status_code=402,
        content={
            "error": "Payment Required",
            "service": service,
            "amount_usdc": amount_usdc,
            "payee": payee_address,
            "protocol": "x402",
            "message": f"Send {amount_usdc} USDC to {payee_address} via Arc Nanopayments",
        },
        headers=headers,
    )
