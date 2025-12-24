import os

from utils.OpenAIClientGenerator import OpenAIClientGenerator
from openai import OpenAI, AsyncOpenAI
client = AsyncOpenAI(base_url=os.getenv("OPENAI_BASE_URL2"), api_key=os.getenv("OPENAI_API_KEY2"))
# client: OpenAI = OpenAIClientGenerator().get_sync_client()
# #
# 编辑图片 - 需要原图和遮罩


async def main():

    completion = await client.chat.completions.create(
        model="gpt-5-search-api",
        web_search_options={},
        messages=[
            {
                "role": "user",
                "content": "https://flowus.cn/9342fa12-d5d0-4f63-8f5f-80d7be6494fe,这篇文章写了什么",
            }
        ],
    )

    print(completion)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
