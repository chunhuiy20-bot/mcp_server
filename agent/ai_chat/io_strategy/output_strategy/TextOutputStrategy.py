from agent.ai_chat.io_strategy.output_strategy.OutputStrategy import OutputStrategy


class TextOutputStrategy(OutputStrategy):
    """文本输出策略"""

    async def process(self, text: str) -> str:
        return text