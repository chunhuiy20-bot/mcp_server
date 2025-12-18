
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import PlainTextResponse
mcp = FastMCP(name="ImageMCP", instructions="图片生成、编辑、理解工具")

# Tools  工具
@mcp.tool()
def add(user_id: int, transaction_category_id: int, transaction_name: str, transaction_amount: float, type: int) -> int:
    """为用户添加一笔资金流水"""
    pass






if __name__ == "__main__":
    print(mcp)
    mcp.run(transport="http", host="0.0.0.0", port=8001)
