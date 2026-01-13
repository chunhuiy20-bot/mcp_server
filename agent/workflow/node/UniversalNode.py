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





