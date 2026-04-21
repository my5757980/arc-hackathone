from .base_agent import BaseAgent, AgentConfig


class DataAnalystAgent(BaseAgent):
    def __init__(self, wallet_id: str = "", wallet_address: str = ""):
        super().__init__(AgentConfig(
            name="DataAnalyst",
            price_usdc=0.003,
            wallet_id=wallet_id,
            wallet_address=wallet_address,
            description="Analyzes data, CSVs, and generates insights. $0.003/task",
        ))

    async def execute(self, task_input: str) -> str:
        prompt = (
            f"You are a data analyst AI agent. Analyze the following and provide "
            f"3 key insights in bullet points (max 100 words total):\n\n{task_input}"
        )
        return self._call_gemini(prompt)
