from abc import ABC

from openai import AsyncOpenAI, OpenAI


class AIClientGenerator(ABC):
    """
    抽象类：AI客户端生成器
    """

    async def get_async_client(self) -> AsyncOpenAI:
        pass

    def get_sync_client(self) -> OpenAI:
        pass
