from .base_agent import BaseAgent, AgentConfig


class TranslatorAgent(BaseAgent):
    def __init__(self, wallet_id: str = "", wallet_address: str = ""):
        super().__init__(AgentConfig(
            name="Translator",
            price_usdc=0.002,
            wallet_id=wallet_id,
            wallet_address=wallet_address,
            description="Translates text between languages. $0.002/task",
        ))

    async def execute(self, task_input: str) -> str:
        prompt = (
            f"You are a professional translator AI agent. Translate the following to English "
            f"(or if already English, to Spanish). Return only the translation:\n\n{task_input}"
        )
        return self._call_gemini(prompt)
