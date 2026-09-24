"""x402: a request is served only for a real, sufficient, recent, unused USDC payment on Arc.

The Arc RPC is faked with httpx.MockTransport, so these tests need no network.
Run from the repo root:  python -m pytest backend/tests
"""
import base64
import json
import time

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from backend.blockchain import x402
from backend.db.models import X402Receipt

pytestmark = pytest.mark.asyncio

PAY_TO = "0x1919ed21ea0c7c56e2a89eb998333395fda5c81e"
PAYER = "0x059ac920d925896cf8b08f9fe9eeae1b7ac625d7"
USDC = "0x3600000000000000000000000000000000000000"
TX = "0x" + "ab" * 32


def header(obj) -> str:
    return base64.b64encode(json.dumps(obj).encode()).decode()


def paid(tx=TX) -> str:
    return header({"x402Version": 1, "scheme": "exact", "network": "arc-testnet", "payload": {"txHash": tx}})


def pad(address: str) -> str:
    return "0x" + "0" * 24 + address[2:].lower()


def transfer_log(to=PAY_TO, units=3000, token=USDC, frm=PAYER):
    return {"address": token, "topics": [x402.TRANSFER_TOPIC, pad(frm), pad(to)], "data": hex(units)}


def receipt(*logs, status="0x1"):
    return {"status": status, "blockNumber": "0x10", "logs": list(logs)}


def fake_arc(rcpt, *, chain_id=5042002, block_age=5, down=False) -> httpx.AsyncClient:
    """An Arc RPC that knows one transaction, TX, mined block_age seconds ago."""
    def handle(request: httpx.Request) -> httpx.Response:
        if down:
            return httpx.Response(503, text="unavailable")
        call = json.loads(request.content)
        method, params = call["method"], call["params"]
        if method == "eth_chainId":
            result = hex(chain_id)
        elif method == "eth_getTransactionReceipt":
            result = rcpt if params[0] == TX else None
        elif method == "eth_getBlockByNumber":
            result = {"timestamp": hex(int(time.time()) - block_age)}
        else:
            return httpx.Response(200, json={"jsonrpc": "2.0", "id": 1, "error": {"message": method}})
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": 1, "result": result})

    return httpx.AsyncClient(transport=httpx.MockTransport(handle))


async def check(x_payment, rpc, amount=0.003):
    async with rpc:
        return await x402.verify_x402_payment(x_payment, amount, PAY_TO, client=rpc)


async def test_the_old_forged_header_is_refused():
    """The previous check served anyone whose base64 JSON claimed a big enough 'amount'."""
    result = await check(header({"amount": "999999999"}), fake_arc(receipt(transfer_log())))
    assert not result.ok and "txHash" in result.reason


@pytest.mark.parametrize("bad", [
    None, "", "not base64 !!", header(["a", "list"]), header({"payload": {"txHash": "0x123"}}),
])
async def test_headers_without_a_valid_tx_hash_are_refused(bad):
    result = await check(bad, fake_arc(receipt(transfer_log())))
    assert not result.ok and result.tx_hash is None


async def test_a_real_payment_is_accepted():
    result = await check(paid(), fake_arc(receipt(transfer_log(units=3000))))
    assert result.ok, result.reason
    assert (result.tx_hash, result.payer, result.amount_usdc) == (TX, PAYER, 0.003)


async def test_top_level_hash_and_upper_case_are_normalised():
    result = await check(header({"txHash": "0x" + "AB" * 32}), fake_arc(receipt(transfer_log())))
    assert result.ok and result.tx_hash == TX


async def test_an_unknown_transaction_is_refused():
    result = await check(paid("0x" + "cd" * 32), fake_arc(receipt(transfer_log())))
    assert not result.ok and "not found" in result.reason


async def test_a_reverted_transaction_is_refused():
    result = await check(paid(), fake_arc(receipt(transfer_log(), status="0x0")))
    assert not result.ok and "failed" in result.reason


async def test_a_payment_to_someone_else_is_refused():
    result = await check(paid(), fake_arc(receipt(transfer_log(to=PAYER))))
    assert not result.ok and "pays 0.0 USDC" in result.reason


async def test_an_underpayment_is_refused():
    result = await check(paid(), fake_arc(receipt(transfer_log(units=2999))))
    assert not result.ok and "0.003 USDC required" in result.reason


async def test_a_look_alike_token_is_refused():
    result = await check(paid(), fake_arc(receipt(transfer_log(token="0x" + "11" * 20))))
    assert not result.ok and "pays 0.0 USDC" in result.reason


async def test_transfers_to_the_payee_in_one_transaction_add_up():
    result = await check(paid(), fake_arc(receipt(transfer_log(units=1000), transfer_log(units=2000))))
    assert result.ok and result.amount_usdc == 0.003


async def test_a_stale_payment_is_refused():
    result = await check(paid(), fake_arc(receipt(transfer_log()), block_age=3600))
    assert not result.ok and "old" in result.reason


async def test_the_wrong_chain_is_refused():
    result = await check(paid(), fake_arc(receipt(transfer_log()), chain_id=60000))
    assert not result.ok and "expected 5042002" in result.reason


async def test_an_rpc_outage_fails_closed():
    result = await check(paid(), fake_arc(receipt(transfer_log()), down=True))
    assert not result.ok and "could not verify" in result.reason


async def test_a_payment_pays_for_one_request_only(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'x402.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(X402Receipt.__table__.create)
    verified = x402.PaymentCheck(True, "ok", TX, PAYER, 0.003)
    async with AsyncSession(engine) as db:
        assert await x402.consume_payment(db, verified, "analyze") is True
    async with AsyncSession(engine) as db:
        assert await x402.consume_payment(db, verified, "analyze") is False
    await engine.dispose()


class FakeAgent:
    def __init__(self, price=0.003, address="0x" + "22" * 20):
        self.price_usdc, self.wallet_address = price, address

    async def execute(self, task_input):
        return "done"

    def increment_tasks(self):
        pass


def orchestrator_whose_payments(monkeypatch, outcome):
    from backend.agents.orchestrator import OrchestratorAgent

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    orch = OrchestratorAgent()
    orch.register_agents({"DataAnalyst": FakeAgent(), "ContentWriter": FakeAgent(0.005)})

    async def pay(**kwargs):
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(orch.nano_client, "initiate_payment", pay)
    return orch


async def test_a_failed_payment_is_simulated_with_no_hash(monkeypatch):
    """It used to be given a made-up 0x hash and recorded as 'confirmed'."""
    orch = orchestrator_whose_payments(monkeypatch, RuntimeError("Circle unavailable"))
    result = await orch.process_task("analyze", "x", "wallet", "0x0")
    assert (result.tx_hash, result.payment_status) == (None, "simulated")
    chain = await orch.chain_task("x", "wallet", "0x0")
    assert [(s["tx_hash"], s["status"]) for s in chain["chain"]] == [(None, "simulated")] * 2


async def test_a_long_payment_state_fits_the_status_column(monkeypatch):
    orch = orchestrator_whose_payments(monkeypatch, {"tx_hash": None, "status": "PENDING_RISK_SCREENING"})
    result = await orch.process_task("analyze", "x", "wallet", "0x0")
    assert result.payment_status == "PENDING_RISK_SCREENI"  # Transaction.status is String(20)


async def test_the_route_answers_a_forged_header_with_402():
    from backend.api.routes.tasks import TaskRequest, x402_execute_task

    response = await x402_execute_task(
        TaskRequest(task_type="analyze", input="x"), x_payment=header({"amount": "999999999"}), db=None
    )
    assert response.status_code == 402
    assert "txHash" in json.loads(response.body)["reason"]
