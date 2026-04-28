"""Base agent class — Gemini 2.5 Flash powered with Function Calling for Circle APIs on Arc."""
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass

from google import genai
from google.genai import types

_gemini_client: genai.Client | None = None

GEMINI_MODEL = "gemini-2.5-flash-preview-04-17"

# Agent registry — used by Function Calling handlers
AGENT_WALLET_IDS: dict[str, str] = {
    "Orchestrator":  os.getenv("ORCHESTRATOR_WALLET_ID",  "8137508b-a29f-5795-ad11-f1e08aa0bedd"),
    "DataAnalyst":   os.getenv("DATA_ANALYST_WALLET_ID",  "76bd15c1-d9c6-58c4-ab78-b8323bd66e15"),
    "ContentWriter": os.getenv("CONTENT_WRITER_WALLET_ID","32493bbc-b42a-56ef-a9dd-cc3ea7b8b0da"),
    "CodeReviewer":  os.getenv("CODE_REVIEWER_WALLET_ID", "12e692a6-f5be-5740-910b-2415a9b245fd"),
    "Translator":    os.getenv("TRANSLATOR_WALLET_ID",    "b44632f8-f56b-57d4-a1c6-7e224e69474d"),
}

AGENT_ADDRESSES: dict[str, str] = {
    "Orchestrator":  os.getenv("ORCHESTRATOR_WALLET_ADDRESS",  "0x1919ed21ea0c7c56e2a89eb998333395fda5c81e"),
    "DataAnalyst":   os.getenv("DATA_ANALYST_WALLET_ADDRESS",  "0x059ac920d925896cf8b08f9fe9eeae1b7ac625d7"),
    "ContentWriter": os.getenv("CONTENT_WRITER_WALLET_ADDRESS","0xf66ec96a7c0ca6a6736ccbc989b6226a9cde43f7"),
    "CodeReviewer":  os.getenv("CODE_REVIEWER_WALLET_ADDRESS", "0x7b022ac63b55b42ee388e2341205f3215098b7f2"),
    "Translator":    os.getenv("TRANSLATOR_WALLET_ADDRESS",    "0x0f1d54b006fa65b1d3afbbac65f2d9dc816b9bbf"),
}

AGENT_PRICES: dict[str, float] = {
    "DataAnalyst": 0.003,
    "ContentWriter": 0.005,
    "CodeReviewer": 0.008,
    "Translator": 0.002,
}

# Gemini Function Calling — Circle API tools Gemini can invoke on Arc
CIRCLE_FUNCTION_DECLARATIONS = [
    types.FunctionDeclaration(
        name="route_to_agent",
        description=(
            "Select the best specialized AI agent to handle a task. "
            "Available agents: DataAnalyst ($0.003/task), ContentWriter ($0.005/task), "
            "CodeReviewer ($0.008/task), Translator ($0.002/task)."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "agent_name": types.Schema(
                    type=types.Type.STRING,
                    description="Agent to route to: DataAnalyst, ContentWriter, CodeReviewer, or Translator",
                ),
                "reason": types.Schema(
                    type=types.Type.STRING,
                    description="One-sentence reason for choosing this agent",
                ),
                "price_usdc": types.Schema(
                    type=types.Type.NUMBER,
                    description="Service price in USDC (e.g. 0.003)",
                ),
            },
            required=["agent_name", "reason", "price_usdc"],
        ),
    ),
    types.FunctionDeclaration(
        name="initiate_payment",
        description=(
            "Transfer USDC from payer wallet to an AI agent wallet on Arc blockchain "
            "via Circle Developer Controlled Wallets. Returns transaction hash."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "payer_wallet_id": types.Schema(
                    type=types.Type.STRING,
                    description="Circle wallet ID of the payer",
                ),
                "to_agent": types.Schema(
                    type=types.Type.STRING,
                    description="Agent receiving USDC: DataAnalyst, ContentWriter, CodeReviewer, or Translator",
                ),
                "amount_usdc": types.Schema(
                    type=types.Type.NUMBER,
                    description="USDC amount (sub-cent, e.g. 0.003)",
                ),
                "memo": types.Schema(
                    type=types.Type.STRING,
                    description="Payment memo describing the task",
                ),
            },
            required=["payer_wallet_id", "to_agent", "amount_usdc", "memo"],
        ),
    ),
    types.FunctionDeclaration(
        name="get_wallet_balance",
        description="Check the current USDC balance of an AI agent wallet on Arc testnet via Circle API.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "agent_name": types.Schema(
                    type=types.Type.STRING,
                    description="Agent name: DataAnalyst, ContentWriter, CodeReviewer, Translator, or Orchestrator",
                ),
            },
            required=["agent_name"],
        ),
    ),
]

CIRCLE_TOOLS = [types.Tool(function_declarations=CIRCLE_FUNCTION_DECLARATIONS)]


async def gemini_function_calling_round(
    prompt: str,
    system_context: str = "",
) -> tuple[str, list[dict]]:
    """
    Standalone Gemini Function Calling loop — used by Orchestrator.
    Gemini autonomously calls Circle API tools (route_to_agent, initiate_payment,
    get_wallet_balance) and Python executes each call against real Circle DCW on Arc.
    Returns (final_text, list_of_function_calls_made).
    """
    executed_calls: list[dict] = []
    try:
        client = _get_gemini_client()
        contents = [types.Content(role="user", parts=[types.Part(text=prompt)])]
        system = system_context or (
            "You are an AI orchestrator with access to Circle APIs on Arc blockchain. "
            "Use the provided functions to route tasks and initiate USDC payments on Arc. "
            "Always call route_to_agent first, then initiate_payment."
        )

        for _ in range(5):
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    tools=CIRCLE_TOOLS,
                    max_output_tokens=400,
                    temperature=0.2,
                    system_instruction=system,
                ),
            )

            fn_calls = [
                p.function_call
                for candidate in response.candidates
                for p in candidate.content.parts
                if p.function_call is not None
            ]

            if not fn_calls:
                return response.text or "", executed_calls

            fn_responses = []
            for fn_call in fn_calls:
                result = await _execute_circle_function(fn_call.name, dict(fn_call.args))
                executed_calls.append({
                    "function": fn_call.name,
                    "args": dict(fn_call.args),
                    "result": result,
                })
                fn_responses.append(
                    types.Part(
                        function_response=types.FunctionResponse(
                            name=fn_call.name,
                            response=result,
                        )
                    )
                )

            contents.append(response.candidates[0].content)
            contents.append(types.Content(role="user", parts=fn_responses))

        return "[max rounds reached]", executed_calls

    except Exception as e:
        return f"[gemini_function_calling_round error: {str(e)[:120]}]", executed_calls


def _get_gemini_client() -> genai.Client:
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))
    return _gemini_client


async def _execute_circle_function(name: str, args: dict) -> dict:
    """Execute a Circle API function call triggered by Gemini Function Calling."""
    if name == "route_to_agent":
        agent = args.get("agent_name", "DataAnalyst")
        return {
            "routed_to": agent,
            "price_usdc": AGENT_PRICES.get(agent, 0.003),
            "wallet_address": AGENT_ADDRESSES.get(agent, ""),
            "reason": args.get("reason", ""),
            "status": "routed",
        }

    elif name == "initiate_payment":
        from ..blockchain.circle_wallets import CircleWalletsClient
        import uuid
        to_agent = args.get("to_agent", "DataAnalyst")
        amount = float(args.get("amount_usdc", 0.003))
        payer_id = args.get("payer_wallet_id", AGENT_WALLET_IDS["Orchestrator"])
        dest_addr = AGENT_ADDRESSES.get(to_agent, "")
        try:
            client = CircleWalletsClient()
            result = await client.transfer_with_fallback(
                source_wallet_id=payer_id,
                dest_address=dest_addr,
                amount_usdc=amount,
                idempotency_key=str(uuid.uuid4()),
                memo=args.get("memo", f"payment:{to_agent}"),
            )
            return {
                "tx_hash": result["txHash"],
                "circle_tx_id": result["id"],
                "amount_usdc": amount,
                "to_agent": to_agent,
                "to_address": dest_addr,
                "status": result["state"],
                "blockchain": "Arc EVM L1 (Chain ID 60000)",
            }
        except Exception as e:
            import hashlib
            return {
                "tx_hash": "0x" + hashlib.sha256(f"{to_agent}{amount}".encode()).hexdigest(),
                "amount_usdc": amount,
                "to_agent": to_agent,
                "status": "simulated",
                "error": str(e)[:80],
            }

    elif name == "get_wallet_balance":
        from ..blockchain.circle_wallets import CircleWalletsClient
        agent = args.get("agent_name", "Orchestrator")
        wallet_id = AGENT_WALLET_IDS.get(agent, "")
        try:
            client = CircleWalletsClient()
            balance = await client.get_balance(wallet_id)
            return {
                "agent_name": agent,
                "balance_usdc": balance,
                "wallet_id": wallet_id,
                "blockchain": "Arc Testnet",
            }
        except Exception:
            return {"agent_name": agent, "balance_usdc": 0.0, "error": "balance unavailable"}

    return {"error": f"Unknown function: {name}"}


@dataclass
class AgentConfig:
    name: str
    price_usdc: float
    wallet_id: str = ""
    wallet_address: str = ""
    description: str = ""


@dataclass
class TaskResult:
    agent: str
    result: str
    cost_usdc: float
    tx_hash: str
    task_type: str
    function_calls: list = None

    def __post_init__(self):
        if self.function_calls is None:
            self.function_calls = []


class BaseAgent(ABC):
    """Abstract base for all AgentFlow agents — powered by Gemini 2.5 Flash with Function Calling."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self._tasks_completed = 0

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def price_usdc(self) -> float:
        return self.config.price_usdc

    @property
    def wallet_id(self) -> str:
        return self.config.wallet_id

    @property
    def wallet_address(self) -> str:
        return self.config.wallet_address

    @abstractmethod
    async def execute(self, task_input: str) -> str:
        """Execute the agent's core task. Returns result string."""
        pass

    def _call_gemini(self, prompt: str) -> str:
        """Call Gemini 2.5 Flash with a prompt — the AI brain of each agent."""
        try:
            client = _get_gemini_client()
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=300,
                    temperature=0.7,
                ),
            )
            return response.text
        except Exception as e:
            return f"[{self.name} Gemini error: {str(e)[:120]}]"

    async def _call_gemini_with_functions(
        self, prompt: str, system_context: str = ""
    ) -> tuple[str, list[dict]]:
        """
        Gemini Function Calling loop — Gemini autonomously calls Circle APIs on Arc.
        Returns (final_text, list_of_function_calls_made).
        """
        executed_calls: list[dict] = []
        try:
            client = _get_gemini_client()
            contents = [types.Content(role="user", parts=[types.Part(text=prompt)])]

            for _ in range(5):  # max 5 function call rounds
                response = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        tools=CIRCLE_TOOLS,
                        max_output_tokens=500,
                        temperature=0.3,
                        system_instruction=system_context or (
                            "You are an AI agent orchestrator with access to Circle APIs on Arc blockchain. "
                            "Use function calls to interact with Circle wallets and route payments. "
                            "Always initiate payments before executing tasks."
                        ),
                    ),
                )

                # Check if Gemini wants to call a function
                fn_calls = [
                    p.function_call
                    for candidate in response.candidates
                    for p in candidate.content.parts
                    if p.function_call is not None
                ]

                if not fn_calls:
                    # No more function calls — return final text
                    text = response.text or ""
                    return text, executed_calls

                # Execute each function call Gemini requested
                fn_responses = []
                for fn_call in fn_calls:
                    result = await _execute_circle_function(fn_call.name, dict(fn_call.args))
                    executed_calls.append({"function": fn_call.name, "args": dict(fn_call.args), "result": result})
                    fn_responses.append(
                        types.Part(
                            function_response=types.FunctionResponse(
                                name=fn_call.name,
                                response=result,
                            )
                        )
                    )

                # Feed function results back to Gemini
                contents.append(response.candidates[0].content)
                contents.append(types.Content(role="user", parts=fn_responses))

            return "[max function call rounds reached]", executed_calls

        except Exception as e:
            return f"[Gemini function calling error: {str(e)[:120]}]", executed_calls

    def increment_tasks(self):
        self._tasks_completed += 1

    @property
    def tasks_completed(self) -> int:
        return self._tasks_completed

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "price_usdc": self.price_usdc,
            "wallet_address": self.wallet_address,
            "tasks_completed": self.tasks_completed,
            "description": self.config.description,
        }
