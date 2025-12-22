from typing import List
from fastmcp import FastMCP
mcp = FastMCP(name="ImageMCP", instructions="生成工具")


# Tools  工具
@mcp.tool
async def image_generation(prompt: str) -> str:
    """图片生成工具"""
    pass


if __name__ == "__main__":
    print(mcp)
    mcp.run(transport="http", host="0.0.0.0", port=8001)
