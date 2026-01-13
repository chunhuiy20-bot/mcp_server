import asyncio
from typing import Dict, Any
from agent.ai_chat.AIChatAbstract import AIChatAbstract
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
            return Result(code=AIBusinessErrorCode.UNSUPPORTED_INPUT_TYPE.code, message=AIBusinessErrorCode.UNSUPPORTED_INPUT_TYPE.message)
        text_input_result = await input_strategy.process(data=user_input, **kwargs)
        if text_input_result.code != 200:
            return text_input_result
        # 2.调用智能体
        text_output = await self.base_agent.chat(text_input_result.data, **kwargs)

        # 3.输出处理
        output_strategy = self._output_strategies.get(output_type)
        if not output_strategy:
            return Result(code=AIBusinessErrorCode.UNSUPPORTED_OUTPUT_TYPE.code, message=AIBusinessErrorCode.UNSUPPORTED_OUTPUT_TYPE.message)
        final_output = await output_strategy.process(text_output)

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
    # response1 = await enhanced_agent.chat(user_input="你好，这道题怎么做", image_list=["https://blog.amazingtalker.com/wp-content/uploads/2022/09/%E4%BB%A3%E5%85%A5%E6%B6%88%E5%8E%BB%E6%B3%95.png"])
    # print(response1)

    # 4. 场景2：语音bytes输入 -> 文本输出
    with open("./io_strategy/input_strategy/simple_speech.mp3", "rb") as f:
        audio_bytes = f.read()  # 这是 bytes 类型
    print(audio_bytes[:10])
    response2 = await enhanced_agent.chat(user_input=audio_bytes, input_type=InputType.VOICE.value, output_type=OutputType.TEXT.value)
    print(response2)

    # 5. 场景3：语音url输入 -> 文本输出
    # response3 = await enhanced_agent.chat(user_input=None, voice_url="https://hdd-ai-image.oss-cn-beijing.aliyuncs.com/local_temp_documents/simple_speech.mp3", input_type=InputType.VOICE.value, output_type=OutputType.TEXT.value)
    # print(response3)



if __name__ == "__main__":
    asyncio.run(main())
