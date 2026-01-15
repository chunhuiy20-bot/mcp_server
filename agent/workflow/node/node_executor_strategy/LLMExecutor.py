# ============ LLM 执行器 ============
from typing import Any
from openai import AsyncOpenAI
from pydantic import BaseModel
from agent.workflow.node.node_config.LLMConfig import LLMConfig
from agent.workflow.node.node_executor_strategy.NodeExecutor import NodeExecutor
from utils.common.factory.DynamicModelFactory import dynamic_model_factory


# noinspection PyMethodMayBeStatic
class LLMExecutor(NodeExecutor):
    """LLM 执行器"""

    def __init__(self):
        self.client: AsyncOpenAI | None = None

    def _init_llm_client(self, config: LLMConfig):
        """初始化 LLM 客户端"""
        if self.client is None:
            self.client = AsyncOpenAI(api_key=config.openai_api_key, base_url=config.openai_api_base)
        return self.client

    def _get_output_schema(self, config: LLMConfig) -> BaseModel:
        """获取输出结构"""
        output_schema = dynamic_model_factory.create(config=config.output_schema, model_name="CustomOutputModel")
        return output_schema

    def _handle_input_data(self, input_data: Any, config: LLMConfig) -> list:
        """处理输入的消息"""
        messages = [{"role": "system", "content": config.system_prompt}]

        # 处理不同输入格式
        if isinstance(input_data, dict):
            # 从 state 提取消息历史
            for msg in input_data.get("messages", []):
                if hasattr(msg, "content"):
                    role = "assistant" if "AI" in msg.__class__.__name__ else "user"
                    messages.append({"role": role, "content": msg.content})
                elif isinstance(msg, dict):
                    messages.append(msg)
        elif isinstance(input_data, str):
            messages.append({"role": "user", "content": input_data})
        elif isinstance(input_data, list):
            messages.extend(input_data)

        return messages

    async def execute(self, input_data: Any, config: LLMConfig) -> Any:
        """执行 LLM 节点"""
        self._init_llm_client(config)
        messages = self._handle_input_data(input_data=input_data, config=config)
        if config.need_structure_output:
            response = await self.client.chat.completions.parse(
                model=config.model,
                messages=messages,
                temperature=config.temperature,
                response_format=self._get_output_schema(config)
            )
            print(response.choices[0].message.parsed)
            return response.choices[0].message.parsed
        else:
            response = await self.client.chat.completions.create(
                model=config.model,
                messages=messages,
                temperature=config.temperature
            )
            print(response.choices[0].message.content)
            return response.choices[0].message.content
