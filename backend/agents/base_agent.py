"""Base agent class — Gemini 2.5 Flash powered, sub-cent USDC payments on Arc."""
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass

from google import genai
from google.genai import types

_gemini_client: genai.Client | None = None

GEMINI_MODEL = "gemini-2.5-flash-preview-04-17"


def _get_gemini_client() -> genai.Client:
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))
    return _gemini_client


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


class BaseAgent(ABC):
    """Abstract base for all AgentFlow agents — powered by Gemini 2.5 Flash."""

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
