from .base_agent import BaseAgent, AgentConfig


class ContentWriterAgent(BaseAgent):
    def __init__(self, wallet_id: str = "", wallet_address: str = ""):
        super().__init__(AgentConfig(
            name="ContentWriter",
            price_usdc=0.005,
            wallet_id=wallet_id,
            wallet_address=wallet_address,
            description="Writes professional content, summaries, and copy. $0.005/task",
        ))

    async def execute(self, task_input: str) -> str:
        prompt = (
            f"You are a professional content writer AI agent. Write a concise, "
            f"compelling response (max 80 words) for:\n\n{task_input}"
        )
        return self._call_gemini(prompt)
