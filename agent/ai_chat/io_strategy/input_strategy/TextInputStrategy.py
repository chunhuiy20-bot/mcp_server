from agent.ai_chat.io_strategy.input_strategy.InputStrategy import InputStrategy


class TextInputStrategy(InputStrategy):
    """文本输入策略"""

    async def process(self, data: str, **kwargs) -> str:
        return data
