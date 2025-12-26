import asyncio
import os
from dotenv import load_dotenv
from fastmcp import FastMCP
from openai import AsyncOpenAI
from mcp_server.common.long_memory_mcp.OpenAIMemorySystem import memory_system

mcp = FastMCP(name="LongMemoryMCP", instructions="长期记忆查询工具")


@mcp.tool
async def search_memories(user_id: str, user_input_extent: str, limit: int = 5):
    """
    如果上下文中没有与用户当前问题相关的信息，可以根据用户问题对长期记忆进行语义搜索，来找到可能的相关答案。
    Args:
        user_id: 用户id
        user_input_extent: 用户输入的自然语言问题或语句，进行同义扩展。例如: 用户是做什么工作的;用户从事什么行业;用户的工作是什么;用户的工作岗位;用户的职业背景
        limit: 返回的相关条数，最高10条
    """
    print("search_memories:", user_id, user_input_extent, limit)
    result = await memory_system.search_memories(user_id=user_id, query=user_input_extent, limit=limit)
    print(result)
    return result


@mcp.tool
async def add_msc_memory(user_id: str, content: str):
    """
    自动收集并存储用户的长期稳定属性信息（MSC = Mostly Static Characteristics），无需提醒用户是否需要收集。

    当用户提到以下类型的个人信息时，应该调用此方法进行收集和存储：

    1. **基本信息**：姓名、年龄、生日、性别、籍贯、居住地
    2. **职业信息**：职业、公司、职位、工作年限、行业
    3. **技能特长**：编程语言、专业技能、证书、擅长领域
    4. **教育背景**：学历、毕业院校、专业、学位
    5. **人际关系**：家庭成员、朋友、同事、导师
    6. **联系方式**：邮箱、电话、社交账号
    7. **兴趣爱好**：运动、音乐、阅读、旅游等长期爱好
    8. **价值观偏好**：工作风格、生活态度、重要原则

    示例触发场景：
    - 用户说："我叫张三" → 调用此方法存储姓名
    - 用户说："我是一个 Python 开发者" → 调用此方法存储职业和技能
    - 用户说："我的生日是 1990年1月1日" → 调用此方法存储生日
    - 用户说："我有一个妹妹叫李四" → 调用此方法存储人际关系
    - 用户说："我的邮箱是 xxx@example.com" → 调用此方法存储联系方式

    注意：
    - 这些信息通常是长期稳定的，不会频繁变化
    - 如果用户提到的是临时状态（如"我今天很累"、"我现在在吃饭"），不应该调用此方法
    - 如果用户明确表示信息有变化（如"我换工作了"），应该更新而不是重复添加

    Args:
        user_id: 用户唯一标识
        content: 要存储的用户属性信息（自然语言描述）

    Returns:
        存储结果
    """
    res = await memory_system.add_memory(user_id=user_id, content=content)
    return res

if __name__ == "__main__":
    print(mcp)
    mcp.run(transport="http", host="0.0.0.0", port=8004)


