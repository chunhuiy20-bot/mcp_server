import asyncio
from typing import Any
from agent.workflow.node.node_config.CodeConfig import CodeConfig
from agent.workflow.node.node_config.LLMConfig import LLMConfig
from agent.workflow.node.node_config.NodeConfig import NodeConfig
from agent.workflow.node.node_executor_strategy.LLMExecutor import LLMExecutor
from agent.workflow.node.node_executor_strategy.NodeExecutor import NodeExecutor
from agent.workflow.node.node_executor_strategy.PythonCodeExecutor import PythonCodeExecutor


# ============ 通用节点 ============
class UniversalNode:
    """通用节点类"""
    def __init__(self, config: NodeConfig):
        self.config = config
        self.executor = self._get_executor()

    def _get_executor(self) -> NodeExecutor:
        """根据节点配置类型获取执行器"""
        node_config = self.config.node_config

        if node_config is None:
            raise ValueError(f"节点 [{self.config.node_name}] 未配置 node_config")

        if isinstance(node_config, LLMConfig):
            return LLMExecutor()
        elif isinstance(node_config, CodeConfig):
            return PythonCodeExecutor()
        else:
            raise ValueError(f"不支持的配置类型: {type(node_config)}")


    async def run_node(self, input_data: Any) -> Any:
        """运行节点"""
        print(f"[{self.config.node_name}] 开始执行，类型: {type(self.config.node_config)}")

        try:
            result = await self.executor.execute(input_data, self.config.node_config)
            print(f"[{self.config.node_name}] 执行成功")
            return result
        except Exception as e:
            print(f"[{self.config.node_name}] 执行失败: {e}")
            raise


# ============ 节点构建器 ============
class UniversalNodeBuilder:
    """通用节点构建器"""
    def __init__(self, node_name: str):
        self._config = NodeConfig(node_name=node_name)

    def with_structure_output(self, llm_config: LLMConfig):
        self._config.node_config = llm_config
        return self

    def with_custom_code_config(self, code_config: CodeConfig):
        self._config.node_config = code_config
        return self

    async def build(self) -> UniversalNode:
        return UniversalNode(self._config)


async def test():
    # 测试编码节点
    code_node = (await UniversalNodeBuilder("data_processor").
                 with_custom_code_config(
                    CodeConfig(
                        custom_code="""
                            print("hello world")
                        """
                    )
                 ).build())
    await code_node.run_node("test_code_node")

    # 测试 LLM 节点（普通文本输出）
    llm_node = (
        await UniversalNodeBuilder("llm_chat")
        .with_structure_output(
            LLMConfig(
                system_prompt="你是一个友好的助手，简洁回答用户问题",
                model="gpt-4.1",
                temperature=0.3
            )
        )
        .build()
    )
    result = await llm_node.run_node("你好，请介绍一下你自己")
    print(f"LLM 回复: {result}")

    # 测试 LLM 节点（结构化输出）
    llm_structure_node = (
        await UniversalNodeBuilder("user_extractor")
        .with_structure_output(
            LLMConfig(
                system_prompt="从用户输入中提取用户信息",
                model="gpt-4.1",
                temperature=0.0,
                need_structure_output=True,
                output_schema={
                    "name": {"type": "str", "description": "用户名称"},
                    "age": {"type": "int", "description": "年龄"},
                    "city": {"type": "Optional[str]", "description": "城市", "required": False}
                }
            )
        )
        .build()
    )
    result = await llm_structure_node.run_node("我叫张三，今年25岁，住在北京")
    print(f"结构化输出: {result}")
    print(f"姓名: {result.name}, 年龄: {result.age}, 城市: {result.city}")


if __name__ == '__main__':
    asyncio.run(test())