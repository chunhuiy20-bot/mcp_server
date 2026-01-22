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
        # ========== 调试代码：检查模型结构 ==========
        print("\n" + "=" * 50)
        print("📋 生成的 Pydantic 模型结构:")
        print("=" * 50)

        # 1. 打印模型名称
        print(f"模型名称: {output_schema.__name__}")

        # 2. 打印所有字段及其类型
        print("\n字段列表:")
        for field_name, field_info in output_schema.model_fields.items():
            print(f"  - {field_name}: {field_info.annotation}")
            if field_info.description:
                print(f"    描述: {field_info.description}")

        # 3. 打印完整的 JSON Schema（最详细）
        print("\n完整 JSON Schema:")
        import json
        schema = output_schema.model_json_schema()
        print(json.dumps(schema, indent=2, ensure_ascii=False))

        # 4. 检查嵌套模型的字段类型
        print("\n嵌套字段详细检查:")
        if hasattr(output_schema, 'model_fields'):
            identity_field = output_schema.model_fields.get('identity')
            if identity_field:
                print(f"  identity 类型: {identity_field.annotation}")
                # 检查 identity 的子字段
                if hasattr(identity_field.annotation, 'model_fields'):
                    print(f"  identity 子字段:")
                    for sub_name, sub_field in identity_field.annotation.model_fields.items():
                        print(f"    - {sub_name}: {sub_field.annotation}")

        print("=" * 50 + "\n")
        # ========== 调试代码结束 ==========

        return output_schema

    def _handle_input_data(self, input_data: Any, config: LLMConfig) -> list:
        """处理输入的消息"""
        messages = [{"role": "system", "content": config.system_prompt}]

        print(f"\n[DEBUG] _handle_input_data 接收到的 input_data 类型: {type(input_data)}")
        print(f"[DEBUG] input_data 内容: {input_data}")

        # 处理不同输入格式
        if isinstance(input_data, dict):
            # 从 state 提取消息历史
            for msg in input_data.get("messages", []):
                if hasattr(msg, "content"):
                    role = "assistant" if "AI" in msg.__class__.__name__ else "user"
                    messages.append({"role": role, "content": msg.content})
                elif isinstance(msg, dict):
                    # 确保 role 和 content 存在且不为空
                    if msg.get("role") and msg.get("content") is not None:
                        messages.append(msg)
                    else:
                        print(f"[WARNING] 跳过无效消息: {msg}")
        elif isinstance(input_data, str):
            messages.append({"role": "user", "content": input_data})
        elif isinstance(input_data, list):
            # 处理列表格式的消息
            for msg in input_data:
                if isinstance(msg, dict):
                    # 确保 role 和 content 存在且不为空
                    if msg.get("role") and msg.get("content") is not None:
                        messages.append(msg)
                    else:
                        print(f"[WARNING] 跳过无效消息: {msg}")
                elif hasattr(msg, "content"):
                    role = "assistant" if "AI" in msg.__class__.__name__ else "user"
                    messages.append({"role": role, "content": msg.content})

        print(f"[DEBUG] 最终构造的 messages: {messages}\n")
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
            print("格式化输出")
            print(response.choices[0].message.parsed)
            return response.choices[0].message.parsed
        else:
            response = await self.client.chat.completions.create(
                model=config.model,
                messages=messages,
                temperature=config.temperature
            )
            print("非格式化输出")
            print(response.choices[0].message.content)
            return response.choices[0].message.content
