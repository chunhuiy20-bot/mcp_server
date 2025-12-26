import asyncio
import os
from dotenv import load_dotenv
from fastmcp import FastMCP
from openai import AsyncOpenAI
from schemas.common.Result import Result

mcp = FastMCP(name="ImageMCP", instructions="生成工具")
load_dotenv()
client: AsyncOpenAI = AsyncOpenAI(base_url=os.getenv("OPENAI_BASE_URL2"), api_key=os.getenv("OPENAI_API_KEY2"))


# Tools  工具
@mcp.tool
async def image_generation(prompt: str, n: int = 1):
    """
    文生图工具
    Args:
        prompt: 优化用户描述后的文生图专业级别术语，例如：'特写，半身人像...'
        n: 生成图片数量，范围 1-10
    """
    try:
        # 使用 Schema 做验证

        tasks = [
            client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            for _ in range(n)
        ]

        responses = await asyncio.gather(*tasks)
        image_urls = [response.data[0].url for response in responses]
        print(f"图片地址：{image_urls}")
        return Result(code=200, message="生成图片成功", data=image_urls)
    except Exception as e:
        return Result(code=500, message=f"生成图片失败:{e}", data=[])



if __name__ == "__main__":
    print(mcp)
    mcp.run(transport="http", host="0.0.0.0", port=8002)
