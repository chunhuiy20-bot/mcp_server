from fastmcp import FastMCP
from dotenv import load_dotenv
import os
from openai import AsyncOpenAI
from schemas.common.Result import Result

load_dotenv()
client = AsyncOpenAI(base_url=os.getenv("OPENAI_BASE_URL2"), api_key=os.getenv("OPENAI_API_KEY2"))
mcp = FastMCP(name="WebSearchMCP", instructions="网络搜索工具")


@mcp.tool
async def web_search(prompt: str):
    """
    网络搜索
    Args:
        prompt: 搜索查询内容，例如：'人工智能最新发展'、'北京天气预报'

    """
    try:

        print(f"WebSearchMCP 接收到请求，入参：{prompt}")
        search_params = {
            "model": "gpt-5-search-api",
            "web_search_options": {},
            "messages": [
                {
                    "role": "user",
                    "content": f"请搜索并总结关于以下问题的信息：{prompt}"
                }
            ]
        }

        # 调用 OpenAI WebSearch API
        response = await client.chat.completions.create(**search_params)
        search_result = response.choices[0].message.content
        print("OpenAI WebSearch API 响应:", search_result)
        return Result(code=200, message="success", data=search_result)

    except Exception as e:
        return Result(code=500, message=str(e))


if __name__ == "__main__":
    print("WebSearchMCP 服务启动")
    mcp.run(transport="http", host="0.0.0.0", port=8001)
