from .base_agent import BaseAgent, AgentConfig


class CodeReviewerAgent(BaseAgent):
    def __init__(self, wallet_id: str = "", wallet_address: str = ""):
        super().__init__(AgentConfig(
            name="CodeReviewer",
            price_usdc=0.008,
            wallet_id=wallet_id,
            wallet_address=wallet_address,
            description="Reviews code for bugs, security, and best practices. $0.008/task",
        ))

    async def execute(self, task_input: str) -> str:
        prompt = (
            f"You are a senior code reviewer AI agent. Review the following code and "
            f"provide 3 specific improvement suggestions (max 100 words):\n\n{task_input}"
        )
        return self._call_gemini(prompt)
