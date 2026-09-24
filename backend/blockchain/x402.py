"""x402 HTTP payment protocol middleware for agent-to-agent payments on Arc.

A caller pays by settling USDC on Arc first, then retrying the request with that transaction in the
X-Payment header: base64 of JSON such as
    {"x402Version": 1, "scheme": "exact", "network": "arc-testnet",
     "payload": {"txHash": "0x...", "signature": "0x..."}}
The server accepts it only when the Arc chain itself shows a successful, recent USDC transfer of at
least the price to the service's payTo address, only once per transaction, and only when `signature` is
the paying wallet's EIP-191 signature of claim_message(txHash). Every transaction hash is public on the
chain, so without the signature anyone watching the payee could claim someone else's payment first.
Contract wallets (for example Circle smart accounts) sign through ERC-1271.
"""
import base64
import json
import os
import re
import time
from dataclasses import dataclass
from decimal import Decimal

import httpx
from eth_abi import encode as abi_encode
from eth_account import Account
from eth_account.messages import defunct_hash_message, encode_defunct
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

USDC_DECIMALS = 6
# keccak256("Transfer(address,address,uint256)"). On Arc, native USDC transfers emit it too.
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
_TX_HASH = re.compile(r"^0x[0-9a-fA-F]{64}$")
# ERC-1271: isValidSignature(bytes32,bytes) selector, which is also the "valid" return value
ERC1271_MAGIC = "0x1626ba7e"


def claim_message(tx_hash: str) -> str:
    """What the paying wallet signs to claim its payment for a request."""
    return f"AgentFlow x402 payment {tx_hash.lower()}"


def _rpc_url() -> str:
    return os.getenv("ARC_RPC_URL", "https://rpc.testnet.arc.network")


def _chain_id() -> int:
    return int(os.getenv("ARC_CHAIN_ID", "5042002"))


def _usdc_contract() -> str:
    # USDC's ERC-20 interface on Arc testnet (symbol USDC, 6 decimals).
    return os.getenv("ARC_USDC_CONTRACT", "0x3600000000000000000000000000000000000000")


def _max_payment_age() -> int:
    return int(os.getenv("X402_MAX_PAYMENT_AGE_SECONDS", "900"))


def _to_units(amount_usdc: float) -> int:
    return int(Decimal(str(amount_usdc)) * 10**USDC_DECIMALS)


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
        "maxAmountRequired": str(_to_units(amount_usdc)),  # USDC has 6 decimals
        "resource": service,
        "description": f"AgentFlow: {service} service",
        "mimeType": "application/json",
        "payTo": payee_address,
        "maxTimeoutSeconds": 60,
        "asset": _usdc_contract(),
        "extra": {"version": "1.0", "scheme": "exact", "signatureMessage": claim_message("<txHash>")},
    }
    encoded = base64.b64encode(json.dumps(payment_details).encode()).decode()
    return {
        "X-Payment-Required": encoded,
        "Accept-Payment-Scheme": "exact",
    }


@dataclass
class PaymentCheck:
    """Outcome of checking an X-Payment header against the Arc chain."""
    ok: bool
    reason: str
    tx_hash: str | None = None
    payer: str | None = None
    amount_usdc: float = 0.0


def _payment_field(payment_header: str | None, name: str):
    """A field of the X-Payment JSON, from `payload` or the top level, or None."""
    if not payment_header:
        return None
    try:
        payment = json.loads(base64.b64decode(payment_header, validate=True))
    except ValueError:  # bad base64, bad UTF-8 or bad JSON
        return None
    if not isinstance(payment, dict):
        return None
    payload = payment.get("payload")
    return (payload.get(name) if isinstance(payload, dict) else None) or payment.get(name)


def parse_payment_header(payment_header: str | None) -> str | None:
    """The transaction hash an X-Payment header carries, lower-cased, or None if it carries none."""
    tx_hash = _payment_field(payment_header, "txHash")
    if isinstance(tx_hash, str) and _TX_HASH.match(tx_hash):
        return tx_hash.lower()
    return None


async def _signed_by(client: httpx.AsyncClient, wallet: str, message: str, signature: str) -> bool:
    """True when `signature` is `wallet`'s signature of `message`: an EOA by ECDSA recovery, a contract
    wallet by asking its ERC-1271 isValidSignature."""
    try:
        if Account.recover_message(encode_defunct(text=message), signature=signature).lower() == wallet:
            return True
    except Exception:  # not a well-formed 65-byte ECDSA signature
        pass
    if (await _rpc(client, "eth_getCode", [wallet, "latest"])) in (None, "0x", "0x0"):
        return False  # an EOA whose recovery did not match
    try:
        sig_bytes = bytes.fromhex(signature.removeprefix("0x"))
    except ValueError:
        return False
    digest = bytes(defunct_hash_message(text=message))
    data = ERC1271_MAGIC + abi_encode(["bytes32", "bytes"], [digest, sig_bytes]).hex()
    try:
        result = await _rpc(client, "eth_call", [{"to": wallet, "data": data}, "latest"])
    except RuntimeError:  # the contract reverted: not a valid signature
        return False
    return isinstance(result, str) and result.lower().startswith(ERC1271_MAGIC)


async def _rpc(client: httpx.AsyncClient, method: str, params: list):
    resp = await client.post(
        _rpc_url(), json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    )
    resp.raise_for_status()
    body = resp.json()
    if body.get("error"):
        raise RuntimeError(f"{method} failed: {body['error']}")
    return body.get("result")


def _hex_int(value) -> int:
    return int(value, 16) if value and value != "0x" else 0


def _topic_address(topic: str) -> str:
    return "0x" + topic[-40:].lower()


async def verify_x402_payment(
    payment_header: str | None,
    expected_amount: float,
    pay_to: str,
    client: httpx.AsyncClient | None = None,
) -> PaymentCheck:
    """Accept only a real, successful, recent USDC transfer on Arc of at least expected_amount to pay_to,
    claimed by the wallet that paid.

    Nothing written in the header is trusted except the transaction hash and the payer's signature: the
    payee, the amount, the payer and the success all come from the chain. This does not mark the payment
    as spent; call consume_payment() once it returns ok.
    """
    tx_hash = parse_payment_header(payment_header)
    if not tx_hash:
        return PaymentCheck(
            False,
            'X-Payment must be base64 JSON like {"payload": {"txHash": "0x..."}} naming a USDC transfer on Arc',
        )
    own_client = client is None
    client = client or httpx.AsyncClient(timeout=15)
    try:
        chain_id = _hex_int(await _rpc(client, "eth_chainId", []))
        if chain_id != _chain_id():
            return PaymentCheck(False, f"RPC {_rpc_url()} is chain {chain_id}, expected {_chain_id()}", tx_hash)
        receipt = await _rpc(client, "eth_getTransactionReceipt", [tx_hash])
        if not receipt:
            return PaymentCheck(
                False, "transaction not found on Arc (not mined yet, or not an Arc transaction)", tx_hash
            )
        if receipt.get("status") != "0x1":
            return PaymentCheck(False, "transaction failed on-chain", tx_hash)

        usdc, payee = _usdc_contract().lower(), pay_to.lower()
        paid, payer = 0, None
        for log in receipt.get("logs") or []:
            topics = [t.lower() for t in log.get("topics") or []]
            if (
                log.get("address", "").lower() == usdc
                and len(topics) == 3
                and topics[0] == TRANSFER_TOPIC
                and _topic_address(topics[2]) == payee
            ):
                paid += _hex_int(log.get("data"))
                payer = payer or _topic_address(topics[1])
        if paid < _to_units(expected_amount):
            return PaymentCheck(
                False,
                f"transaction pays {paid / 10**USDC_DECIMALS} USDC to {pay_to}; {expected_amount} USDC required",
                tx_hash,
            )

        block = await _rpc(client, "eth_getBlockByNumber", [receipt["blockNumber"], False])
        age = time.time() - _hex_int(block["timestamp"])
        if age > _max_payment_age():
            return PaymentCheck(
                False, f"payment is {int(age)}s old; it must be under {_max_payment_age()}s", tx_hash
            )

        signature = _payment_field(payment_header, "signature")
        if not isinstance(signature, str) or not signature:
            return PaymentCheck(
                False,
                "X-Payment must carry payload.signature: the paying wallet's signature of "
                f'"{claim_message(tx_hash)}"',
                tx_hash,
            )
        if not await _signed_by(client, payer, claim_message(tx_hash), signature):
            return PaymentCheck(False, f"the signature is not from the payer {payer}", tx_hash)
        return PaymentCheck(True, "ok", tx_hash, payer, paid / 10**USDC_DECIMALS)
    except (httpx.HTTPError, RuntimeError, KeyError, TypeError, ValueError) as e:
        return PaymentCheck(False, f"could not verify the payment on Arc: {e}", tx_hash)
    finally:
        if own_client:
            await client.aclose()


async def consume_payment(db, check: PaymentCheck, service: str) -> bool:
    """Mark a verified payment as spent. False when that transaction already paid for a request."""
    from ..db.models import X402Receipt

    db.add(
        X402Receipt(
            tx_hash=check.tx_hash, payer=check.payer, amount_usdc=check.amount_usdc, service=service[:50]
        )
    )
    try:
        await db.commit()
        return True
    except IntegrityError:
        await db.rollback()
        return False


async def x402_payment_response(
    payee_address: str, amount_usdc: float, service: str, reason: str | None = None
):
    """Return a 402 Payment Required response."""
    headers = build_x402_header(payee_address, amount_usdc, service)
    content = {
        "error": "Payment Required",
        "service": service,
        "amount_usdc": amount_usdc,
        "payee": payee_address,
        "protocol": "x402",
        "message": (
            f"Send at least {amount_usdc} USDC to {payee_address} on Arc testnet (chain {_chain_id()}), "
            'then retry with header X-Payment: base64 of {"payload": {"txHash": "0x...", "signature": "0x..."}}, '
            f'where signature is the paying wallet\'s signature of "{claim_message("<txHash>")}"'
        ),
    }
    if reason:
        content["reason"] = reason
    return JSONResponse(status_code=402, content=content, headers=headers)
