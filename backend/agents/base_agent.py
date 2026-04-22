"""Base agent class for all AgentFlow agents."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))


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
    """Abstract base for all AgentFlow agents."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.model = genai.GenerativeModel("gemini-2.5-flash")
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
        """Call Gemini Flash with a prompt."""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"[Agent {self.name} error: {str(e)[:100]}]"

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
