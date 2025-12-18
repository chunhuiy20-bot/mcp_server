from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent

client = MultiServerMCPClient(
    {
        "TransactionMCP": {  # 修改为正确的服务名
            "transport": "http",
            "url": "http://localhost:8001/mcp"
        }
    }
)


class UserContextTool:

    def __init__(self, original_tool, user_id):
        self.original_tool = original_tool
        self.user_id = user_id
        self.name = original_tool.name
        self.description = original_tool.description

        # 只复制必要的属性，避免Pydantic警告
        safe_attrs = [
            'args_schema', 'return_direct', 'verbose', 'callbacks',
            'tags', 'metadata', 'handle_tool_error', 'handle_validation_error'
        ]

        for attr in safe_attrs:
            if hasattr(original_tool, attr):
                try:
                    setattr(self, attr, getattr(original_tool, attr))
                except (AttributeError, TypeError, ValueError):
                    # 只捕获可能发生的属性操作相关异常
                    # 属性不存在、类型不匹配、值错误等
                    pass
                except Exception as e:
                    # 对于其他异常，至少记录日志
                    print(f"警告: 复制属性 {attr} 时发生意外错误: {e}")
                    # 可以选择不传递，或者根据情况处理

    async def ainvoke(self, input_dict):
        """异步调用方法"""
        print(f"🔧 [工具增强] 原始参数: {input_dict}")
        # 创建新的字典，避免修改原始参数
        enhanced_input = input_dict.copy()
        enhanced_input["user_id"] = self.user_id
        print(f"🔧 [工具增强] 增强后参数: {enhanced_input}")
        return await self.original_tool.ainvoke(enhanced_input)

    async def invoke(self, input_dict):
        """保持兼容性的调用方法"""
        return await self.ainvoke(input_dict)

    def get_name(self):
        return self.original_tool.get_name()

    def __getattr__(self, name):
        """代理其他属性访问到原始工具"""
        return getattr(self.original_tool, name)


def enhance_tools_with_user_context(tools, target_user_id):
    """为工具增强用户上下文，自动填入user_id"""
    enhanced_tools = []

    for tool in tools:
        # 创建工具的包装器，自动注入user_id
        enhanced_tool = UserContextTool(tool, target_user_id)
        enhanced_tools.append(enhanced_tool)

    return enhanced_tools


async def test():
    print("=== 获取原始工具 ===")
    tools = await client.get_tools(server_name="TransactionMCP")

    for i, tool in enumerate(tools):
        print(f"工具 {i + 1}:")
        print(f"  名称: {tool.get_name()}")
        print(f"  描述: {tool.description}")
        print(f"  类型: {type(tool)}")
        print(f"  支持异步: {hasattr(tool, 'ainvoke')}")
        print()

    print("=== 增强工具（模拟用户ID: 12345）===")
    user_id = 12345
    enhanced_tools = enhance_tools_with_user_context(tools, user_id)

    for i, enhanced_tool in enumerate(enhanced_tools):
        print(f"增强工具 {i + 1}:")
        print(f"  名称: {enhanced_tool.get_name()}")
        print(f"  描述: {enhanced_tool.description}")
        print(f"  用户ID: {enhanced_tool.user_id}")
        print(f"  类型: {type(enhanced_tool)}")
        print(f"  支持异步: {hasattr(enhanced_tool, 'ainvoke')}")
        print()

    print("=== 测试工具调用 ===")
    # 假设第一个工具是 add_transaction
    if enhanced_tools:
        first_tool = enhanced_tools[0]
        print(f"测试调用工具: {first_tool.get_name()}")

        # 模拟调用参数（不包含user_id）
        test_params = {
            "transaction_category_id": 1,
            "transaction_name": "测试消费",
            "transaction_amount": 50.0,
            "type": 1
        }

        print(f"调用前 - 原始参数: {test_params}")

        try:
            # 使用异步调用
            result = await first_tool.ainvoke(test_params)
            print(f"✅ 调用成功!")
            print(f"📝 调用结果: {result}")
        except Exception as e:
            print(f"❌ 调用失败: {e}")
            import traceback
            traceback.print_exc()


async def test_all_tools():
    """测试所有工具"""
    print("\n=== 测试所有工具 ===")

    tools = await client.get_tools(server_name="TransactionMCP")
    enhanced_tools = enhance_tools_with_user_context(tools, 12345)

    # 测试添加交易
    add_tool = None
    query_tool = None

    # 找到对应的工具
    for tool in enhanced_tools:
        if 'add_transaction' in tool.get_name():
            add_tool = tool
        elif 'query_transactions' in tool.get_name():
            query_tool = tool
        elif "test_dont_user_id" in tool.get_name():
            test_dont_user_id = tool

    if add_tool:
        print(f"\n🧪 测试 {add_tool.get_name()}")
        try:
            result = await add_tool.ainvoke({
                "transaction_category_id": 1,
                "transaction_name": "午餐",
                "transaction_amount": 25.0,
                "type": 1,
                "remark": "公司食堂"
            })
            print(f"✅ 添加交易成功:")
            print(result)
        except Exception as e:
            print(f"❌ 添加交易失败: {e}")

    # 测试查询交易
    if query_tool:
        print(f"\n🧪 测试 {query_tool.get_name()}")
        try:
            result = await query_tool.ainvoke({
                "limit": 5,
                "type": 1  # 只查询支出
            })
            print(f"✅ 查询交易成功:")
            print(result)
        except Exception as e:
            print(f"❌ 查询交易失败: {e}")


async def test_user_separation():
    """测试用户数据隔离"""
    print("\n=== 测试用户数据隔离 ===")

    tools = await client.get_tools(server_name="TransactionMCP")

    # 为不同用户创建增强工具
    user1_tools = enhance_tools_with_user_context(tools, 11111)
    user2_tools = enhance_tools_with_user_context(tools, 22222)

    # 用户1添加交易
    if user1_tools:
        add_tool1 = user1_tools[0]
        print("👤 用户1添加交易:")
        try:
            result1 = await add_tool1.ainvoke({
                "transaction_category_id": 1,
                "transaction_name": "用户1的午餐",
                "transaction_amount": 30.0,
                "type": 1
            })
            print(f"✅ 用户1: {result1}")
        except Exception as e:
            print(f"❌ 用户1失败: {e}")

    # 用户2添加交易
    if user2_tools:
        add_tool2 = user2_tools[0]
        print("\n👤 用户2添加交易:")
        try:
            result2 = await add_tool2.ainvoke({
                "transaction_category_id": 2,
                "transaction_name": "用户2的交通",
                "transaction_amount": 5.0,
                "type": 1
            })
            print(f"✅ 用户2: {result2}")
        except Exception as e:
            print(f"❌ 用户2失败: {e}")

    # 分别查询两个用户的数据
    if len(user1_tools) > 1 and len(user2_tools) > 1:
        query_tool1 = user1_tools[1]
        query_tool2 = user2_tools[1]

        print("\n👤 用户1查询自己的数据:")
        try:
            result1 = await query_tool1.ainvoke({"limit": 3})
            print("✅ 用户1的数据:")
            print(result1)
        except Exception as e:
            print(f"❌ 用户1查询失败: {e}")

        print("\n👤 用户2查询自己的数据:")
        try:
            result2 = await query_tool2.ainvoke({"limit": 3})
            print("✅ 用户2的数据:")
            print(result2)
        except Exception as e:
            print(f"❌ 用户2查询失败: {e}")


if __name__ == "__main__":
    import asyncio
    import warnings

    print("🚀 开始测试工具增强功能（清理版本）\n")

    try:
        asyncio.run(test())
        asyncio.run(test_all_tools())
        asyncio.run(test_user_separation())
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback

        traceback.print_exc()