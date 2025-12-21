from typing import List
from fastmcp import FastMCP
mcp = FastMCP(name="ImageMCP", instructions="图片理解、识别、生成、编辑工具")

# Tools  工具
@mcp.tool
async def visual_understanding(image_url: List[str]) -> str:
    """图片理解与识别工具"""
    pass

@mcp.tool
async def image_generation(prompt: str) -> str:
    """图片生成工具"""
    pass

async def image_editing(image_url: str, prompt: str) -> str:
    """图片编辑工具"""
    pass






if __name__ == "__main__":
    print(mcp)
    mcp.run(transport="http", host="0.0.0.0", port=8001)
