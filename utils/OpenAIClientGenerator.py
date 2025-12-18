from dotenv import load_dotenv
import os
load_dotenv()
from openai import AsyncOpenAI, OpenAI

from utils.AIClientGenerator import AIClientGenerator


class OpenAIClientGenerator(AIClientGenerator):
    def __init__(self):
        # 官方 API 配置
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL")
        # 非官方 API 配置（例如反代 / 第三方）
        self.unofficial_api_key = os.getenv("UNOFFICIAL_OPENAI_API_KEY")
        self.unofficial_base_url = os.getenv("UNOFFICIAL_OPENAI_BASE_URL")

        # 缓存客户端实例
        self._async_client = None
        self._sync_client = None
        self._async_unofficial_client = None
        self._sync_unofficial_client = None

    async def get_async_client(self) -> AsyncOpenAI:
        """获取官方异步客户端（单例）"""
        if self._async_client is None:
            self._async_client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._async_client

    def get_sync_client(self) -> OpenAI:
        """获取官方同步客户端（单例）"""
        if self._sync_client is None:
            self._sync_client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._sync_client


"""
    测试使用案例
"""

async def main():
    # 创建生成器
    generator: OpenAIClientGenerator = OpenAIClientGenerator()

    # 获取官方异步客户端
    async_client = await generator.get_async_unofficial_client()
    # #
    # 调用 Chat Completions
    resp = await async_client.chat.completions.create(
        model="claude-sonnet-4-20250514",
        messages=[
            {"role": "user", "content": "你好,你目前是那个模型"}
        ]
    )
    print("非官方 API 响应:", resp.choices[0].message.content)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

