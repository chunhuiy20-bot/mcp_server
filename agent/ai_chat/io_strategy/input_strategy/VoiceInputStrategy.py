from agent.ai_chat.io_strategy.input_strategy.InputStrategy import InputStrategy


class VoiceInputStrategy(InputStrategy):
    """语音输入策略"""

    async def process(self, data: bytes) -> str:
        # TODO: 集成语音识别服务（如 OpenAI Whisper, Azure Speech, 讯飞等）
        # text = await self._speech_to_text(data)
        print("语音识别中...")
        return "这是语音识别后的文本: 你好"

    async def _speech_to_text(self, audio: bytes) -> str:
        """调用语音识别API"""
        # 实现语音识别逻辑
        pass