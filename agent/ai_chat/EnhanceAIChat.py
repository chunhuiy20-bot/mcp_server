import asyncio
from typing import Dict, Any
from agent.AIChatAbstract import AIChatAbstract
from agent.ai_chat.io_strategy.input_strategy.InputStrategy import InputStrategy
from agent.ai_chat.io_strategy.input_strategy.InputType import InputType
from agent.ai_chat.io_strategy.input_strategy.TextInputStrategy import TextInputStrategy
from agent.ai_chat.io_strategy.input_strategy.VoiceInputStrategy import VoiceInputStrategy
from agent.ai_chat.io_strategy.output_strategy.OutputStrategy import OutputStrategy
from agent.ai_chat.io_strategy.output_strategy.OutputType import OutputType
from agent.ai_chat.io_strategy.output_strategy.TextOutputStrategy import TextOutputStrategy
from agent.ai_chat.io_strategy.output_strategy.VoiceOutputStrategy import VoiceOutputStrategy
from agent.error_code.AiBussnessErrorCode import AIBusinessErrorCode
from agent.react_agent.ReactAgentBuilder import ReactAgentBuilder, MemoryConfig, LLMConfig, MCPConfig
from schemas.common.Result import Result


class EnhancedAIChat:
    """
    增强的AI聊天接口，继承自AIChatAbstract
    """

    def __init__(self, base_agent: AIChatAbstract):
        """
        :param base_agent: 基础智能体（如 ReactAgent）
        """
        self.base_agent = base_agent

        # 注册输入策略
        self._input_strategies: Dict[str, InputStrategy] = {
            "text": TextInputStrategy(),
            "voice": VoiceInputStrategy(),
        }

        # 注册输出策略
        self._output_strategies: Dict[str, OutputStrategy] = {
            "text": TextOutputStrategy(),
            "voice": VoiceOutputStrategy()
        }


    async def chat(self, user_input: Any, input_type: str = InputType.TEXT.value, output_type: str = OutputType.TEXT.value, **kwargs):
        """
        聊天方法
        :param output_type:
        :param input_type:
        :param user_input:
        :param kwargs: 其他参数
        :return: 聊天结果
        """
        # 1. 输入处理
        input_strategy = self._input_strategies.get(input_type)
        if not input_strategy:
            return Result(code = AIBusinessErrorCode.UNSUPPORTED_INPUT_TYPE.code, message = AIBusinessErrorCode.UNSUPPORTED_INPUT_TYPE.message)
        text_input = await input_strategy.process(user_input)
        print(f"输入处理完成，转换后的文本: {text_input}")

        # 2.调用智能体
        text_output = await self.base_agent.chat(text_input, **kwargs)
        print(f"ai输出后的文本: {text_output}")

        # 3.输出处理
        output_strategy = self._output_strategies.get(output_type)
        if not output_strategy:
            return Result(code = AIBusinessErrorCode.UNSUPPORTED_OUTPUT_TYPE.code, message = AIBusinessErrorCode.UNSUPPORTED_OUTPUT_TYPE.message)
        final_output = await output_strategy.process(text_output)
        print(f"输出处理完成，最终输出: {final_output}")
        return final_output

    async def chat_stream(self, chat_input: str, **kwargs):
        """
        流式聊天方法
        :param chat_input:
        :param kwargs: 其他参数
        :return: 聊天结果
        """
        pass

    def register_input_strategy(self, input_type: str, strategy: InputStrategy):
        """动态注册新输入策略"""
        self._input_strategies[input_type] = strategy

    def register_output_strategy(self, output_type: str, strategy: OutputStrategy):
        """动态注册新输出策略"""
        self._output_strategies[output_type] = strategy


async def main():
    # 1. 创建基础 ReactAgent
    react_agent = await (
        ReactAgentBuilder(agent_name="test_agent")
        .with_memory_config(MemoryConfig(enable_memory=True))
        .with_llm_config(LLMConfig())
        .with_mcp_config(
            MCPConfig(
                server_name="TransactionMCP",
                server_url="http://localhost:8001/mcp",
                transport="http",
                is_necessary=True
            )
        )
        .with_system_prompt("你叫tom，是用户的智能助手")
        .build("1008611")
    )

    # 2. 创建增强的聊天代理
    enhanced_agent = EnhancedAIChat(react_agent)

    # 3. 场景1：文本输入 -> 文本输出（默认）
    response1 = await enhanced_agent.chat("你好，介绍一下自己",)
    print(response1)


if __name__ == "__main__":
    asyncio.run(main())