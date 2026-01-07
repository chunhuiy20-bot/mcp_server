# ============ LLM 执行器 ============
from typing import Any
from openai import AsyncOpenAI
from pydantic import BaseModel
from agent.workflow.node.node_config.LLMConfig import LLMConfig
from agent.workflow.node.node_executor_strategy.NodeExecutor import NodeExecutor
from utils.common.factory.DynamicModelFactory import dynamic_model_factory


class LLMExecutor(NodeExecutor):
    """LLM 执行器"""

    def __init__(self):
        self.client: AsyncOpenAI | None = None

    def _init_llm_client(self, config: LLMConfig):
        """初始化 LLM 客户端"""
        if self.client is None:
            self.client = AsyncOpenAI(api_key=config.openai_api_key, base_url=config.openai_api_base)
        return self.client

    # noinspection PyMethodMayBeStatic
    def _get_output_schema(self, config: LLMConfig) -> BaseModel:
        """获取输出结构"""
        output_schema = dynamic_model_factory.create(config=config.output_schema, model_name="CustomOutputModel")
        return output_schema

    async def execute(self, input_data: Any, config: LLMConfig) -> Any:
        """执行 LLM 节点"""
        self._init_llm_client(config)
        if config.need_structure_output:
            # 结构化输出
            response = await self.client.chat.completions.parse(
                model=config.model,
                messages=[
                    {"role": "system", "content": config.system_prompt},
                    {"role": "user", "content": input_data}
                ],
                temperature=config.temperature,
                response_format=self._get_output_schema(config)
            )
            return response.choices[0].message.parsed
        else:
            # 非结构化输出
            response = await self.client.chat.completions.create(
                model=config.model,
                messages=[
                    {"role": "system", "content": config.system_prompt},
                    {"role": "user", "content": input_data}
                ],
                temperature=config.temperature
            )
            return response.choices[0].message.content
