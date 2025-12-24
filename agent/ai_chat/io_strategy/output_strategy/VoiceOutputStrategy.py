from agent.ai_chat.io_strategy.output_strategy.OutputStrategy import OutputStrategy


class VoiceOutputStrategy(OutputStrategy):
    """语音输出策略"""

    # async def process(self, text: str) -> bytes:
    #     # TODO: 集成TTS服务（如 OpenAI TTS, Azure TTS, 讯飞等）
    #     # audio = await self._text_to_speech(text)
    #     print("生成语音中...")
    #     return

    async def process(self, text: str) -> str:
        # TODO: 集成TTS服务（如 OpenAI TTS, Azure TTS, 讯飞等）
        # audio = await self._text_to_speech(text)
        print("生成语音中...")
        return "你好"

    async def _text_to_speech(self, text: str) -> bytes:
        """调用TTS API"""
        # 实现TTS逻辑
        pass
