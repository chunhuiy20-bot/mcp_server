import asyncio
from datetime import datetime
from typing import Any, Optional, Iterator, Sequence
from concurrent.futures import ThreadPoolExecutor
import uuid
from langchain.agents import create_agent
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, BaseMessage, AIMessage, ToolMessage
from config.db.redis.RedisClient import AsyncRedisClient
from langgraph.checkpoint.base import BaseCheckpointSaver, CheckpointTuple
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import Checkpoint, CheckpointMetadata, ChannelVersions


class CustomRedisCheckpointAdapter(BaseCheckpointSaver):
    """
    基于 Redis 消息队列的检查点适配器
    自动将检查点中的消息同步到 Redis 消息队列
    从 config 中自动读取 thread_id 作为 user_id
    """

    def __init__(self, redis_client: AsyncRedisClient, max_length: int = 1000):
        super().__init__()
        self.redis_client = redis_client
        # 内部使用内存检查点存储完整状态
        from langgraph.checkpoint.memory import MemorySaver
        self._memory_saver = MemorySaver()
        # 创建线程池用于执行异步操作
        self._executor = ThreadPoolExecutor(max_workers=1)
        self.max_length = max_length

    def _get_user_id_from_config(self, config: RunnableConfig) -> str:
        """从 config 中获取 user_id（即 thread_id）"""
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            raise ValueError("config 中必须包含 'configurable.thread_id'")
        return str(thread_id)

    def _run_async(self, coro):
        """在同步方法中运行异步函数"""
        try:
            # 尝试获取当前事件循环
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环正在运行，使用线程池执行
                future = self._executor.submit(asyncio.run, coro)
                return future.result()
            else:
                # 如果事件循环未运行，直接运行
                return loop.run_until_complete(coro)
        except RuntimeError:
            # 没有事件循环，创建新的
            return asyncio.run(coro)

    def _generate_checkpoint_id(self) -> str:
        """生成有效的 UUID 格式的 checkpoint ID"""
        return str(uuid.uuid4())

    def _validate_and_fix_messages(self, messages: list[BaseMessage]) -> list[BaseMessage]:
        """
        验证并修复消息列表的完整性
        确保每个包含 tool_calls 的 AIMessage 都有对应的 ToolMessage
        """
        if not messages:
            return messages

        validated_messages = []
        pending_tool_calls = {}  # {tool_call_id: AIMessage}

        for msg in messages:
            if isinstance(msg, AIMessage):
                # 检查是否有 tool_calls
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    # 记录待处理的 tool_call_ids
                    for tool_call in msg.tool_calls:
                        tool_call_id = tool_call.get('id') if isinstance(tool_call, dict) else getattr(tool_call, 'id',
                                                                                                       None)
                        if tool_call_id:
                            pending_tool_calls[tool_call_id] = msg
                    validated_messages.append(msg)
                else:
                    # 没有 tool_calls 的 AIMessage，直接添加
                    # 但如果之前有待处理的 tool_calls，先清理它们
                    if pending_tool_calls:
                        # 有未完成的工具调用，移除最后一个包含 tool_calls 的 AIMessage
                        # 因为工具调用没有完成，不应该保留这个不完整的对话
                        validated_messages = [m for m in validated_messages
                                              if not (isinstance(m, AIMessage) and
                                                      hasattr(m, 'tool_calls') and m.tool_calls)]
                        pending_tool_calls.clear()
                    validated_messages.append(msg)

            elif isinstance(msg, ToolMessage):
                # 工具响应消息
                tool_call_id = getattr(msg, 'tool_call_id', None)
                if tool_call_id and tool_call_id in pending_tool_calls:
                    # 找到了对应的工具调用，移除待处理记录
                    del pending_tool_calls[tool_call_id]
                    validated_messages.append(msg)
                elif tool_call_id:
                    # 工具调用 ID 不匹配，可能是孤立的工具消息，跳过
                    continue
                else:
                    # 没有 tool_call_id，直接添加
                    validated_messages.append(msg)

            else:
                # 其他类型消息（HumanMessage等），直接添加
                # 但如果之前有待处理的 tool_calls，说明对话不完整
                if pending_tool_calls:
                    # 移除最后一个包含 tool_calls 的 AIMessage
                    validated_messages = [m for m in validated_messages
                                          if not (isinstance(m, AIMessage) and
                                                  hasattr(m, 'tool_calls') and m.tool_calls)]
                    pending_tool_calls.clear()
                validated_messages.append(msg)

        # 如果最后还有未完成的 tool_calls，移除最后一个包含 tool_calls 的 AIMessage
        if pending_tool_calls:
            validated_messages = [m for m in validated_messages
                                  if not (isinstance(m, AIMessage) and
                                          hasattr(m, 'tool_calls') and m.tool_calls)]

        return validated_messages

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """
        获取检查点：
        1. 先从内存检查点获取完整结构
        2. 从 Redis 读取历史消息
        3. 验证并修复消息完整性
        4. 如果内存检查点存在，合并消息；否则创建新检查点
        """
        # 从 config 中获取 user_id
        user_id = self._get_user_id_from_config(config)

        # 先从内存检查点获取（获取完整结构和元数据）
        memory_tuple = self._memory_saver.get_tuple(config)

        # 从 Redis 读取历史消息
        try:
            messages = self._run_async(
                self.redis_client.async_get_message_queue(user_id)
            )
            # 验证并修复消息完整性
            messages = self._validate_and_fix_messages(messages)
        except Exception as e:
            print(f"读取历史消息失败: {e}")
            messages = []

        # 如果内存检查点存在，使用它的完整结构，只更新消息
        if memory_tuple:
            checkpoint_dict = memory_tuple.checkpoint

            # 使用内存检查点的 ID（应该是有效的 UUID）
            checkpoint_id = checkpoint_dict.get("id")
            if not checkpoint_id or checkpoint_id == "head":
                checkpoint_id = self._generate_checkpoint_id()

            # 优先使用内存检查点中的消息（它们应该是完整的）
            # 但如果 Redis 中有更新的消息，使用 Redis 的消息
            memory_messages = checkpoint_dict.get("channel_values", {}).get("messages", [])
            if memory_messages:
                # 使用内存检查点的消息（应该更完整）
                final_messages = memory_messages
            else:
                # 使用 Redis 的消息
                final_messages = messages

            # 创建新检查点，保留所有结构信息，只更新消息
            checkpoint = Checkpoint(
                v=checkpoint_dict.get("v", 1),
                ts=checkpoint_dict.get("ts", datetime.now().isoformat()),
                id=checkpoint_id,
                channel_values={
                    **checkpoint_dict.get("channel_values", {}),
                    "messages": final_messages
                },
                channel_versions=checkpoint_dict.get("channel_versions", {}),
                versions_seen=checkpoint_dict.get("versions_seen", {})
            )

            # 确保元数据包含必要字段
            metadata = memory_tuple.metadata.copy() if memory_tuple.metadata else {}
            if "step" not in metadata:
                metadata["step"] = 0

            # 更新 config 中的 checkpoint_id
            updated_config = config.copy()
            updated_config.setdefault("configurable", {})["checkpoint_id"] = checkpoint_id

            return CheckpointTuple(
                config=updated_config,
                checkpoint=checkpoint,
                metadata=metadata,
                parent_config=memory_tuple.parent_config,
                pending_writes=memory_tuple.pending_writes or []
            )

        # 如果没有内存检查点，但有历史消息，创建新检查点
        if messages:
            # 生成新的 UUID checkpoint_id
            checkpoint_id = self._generate_checkpoint_id()
            checkpoint = Checkpoint(
                v=1,
                ts=datetime.now().isoformat(),
                id=checkpoint_id,
                channel_values={"messages": messages},
                channel_versions={},
                versions_seen={}
            )

            # 创建包含必要字段的元数据
            metadata = {
                "step": 0,  # 初始步骤
                "source": "input"  # 来源
            }

            # 更新 config 中的 checkpoint_id
            updated_config = config.copy()
            updated_config.setdefault("configurable", {})["checkpoint_id"] = checkpoint_id

            return CheckpointTuple(
                config=updated_config,
                checkpoint=checkpoint,
                metadata=metadata,
                parent_config=None,
                pending_writes=[]
            )

        # 既没有内存检查点，也没有历史消息，返回 None（让 LangGraph 创建新的）
        return None

    def put(
            self,
            config: RunnableConfig,
            checkpoint: Checkpoint,
            metadata: CheckpointMetadata,
            new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """
        保存检查点：
        1. 保存到内存检查点
        2. 提取消息并同步到 Redis 消息队列
        """
        # 从 config 中获取 user_id
        user_id = self._get_user_id_from_config(config)

        # 先保存到内存检查点（保留完整结构和元数据）
        saved_config = self._memory_saver.put(config, checkpoint, metadata, new_versions)

        # 提取消息并同步到 Redis
        channel_values = checkpoint.get("channel_values", {})
        if "messages" in channel_values:
            messages = channel_values["messages"]
            # 验证消息完整性
            messages = self._validate_and_fix_messages(messages)

            try:
                # 完全替换 Redis 中的消息（使用完整消息列表）
                self._run_async(
                    self.redis_client.async_clear_message_queue(user_id)
                )
                # 写入所有消息（确保完整性）
                for msg in messages:
                    self._run_async(
                        self.redis_client.async_add_message_to_queue(
                            user_id, msg, self.max_length
                        )
                    )
            except Exception as e:
                print(f"同步消息到Redis失败: {e}")

        return saved_config

    def put_writes(
            self,
            config: RunnableConfig,
            writes: Sequence[tuple[str, Any]],
            task_id: str,
            task_path: str = "",
    ) -> None:
        """
        保存中间写入：
        1. 保存到内存检查点
        2. 如果是消息类型的写入，同步到 Redis 消息队列
        """
        # 保存到内存检查点
        self._memory_saver.put_writes(config, writes, task_id, task_path)

        # 注意：中间写入可能不完整，不应该立即写入 Redis
        # 应该在 put() 方法中写入完整的消息列表
        # 这里暂时不写入，避免不完整的消息

    def list(self, config, *, filter=None, before=None, limit=None) -> Iterator[CheckpointTuple]:
        """列出检查点（从内存检查点）"""
        return self._memory_saver.list(config, filter=filter, before=before, limit=limit)

    # 异步方法
    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """异步获取检查点"""
        # 从 config 中获取 user_id
        user_id = self._get_user_id_from_config(config)

        # 先从内存检查点获取
        memory_tuple = await self._memory_saver.aget_tuple(config)

        # 从 Redis 读取历史消息
        messages = await self.redis_client.async_get_message_queue(user_id)
        # 验证并修复消息完整性
        messages = self._validate_and_fix_messages(messages)

        # 如果内存检查点存在，使用它的结构
        if memory_tuple:
            checkpoint_dict = memory_tuple.checkpoint

            checkpoint_id = checkpoint_dict.get("id")
            if not checkpoint_id or checkpoint_id == "head":
                checkpoint_id = self._generate_checkpoint_id()

            # 优先使用内存检查点的消息
            memory_messages = checkpoint_dict.get("channel_values", {}).get("messages", [])
            final_messages = memory_messages if memory_messages else messages

            checkpoint = Checkpoint(
                v=checkpoint_dict.get("v", 1),
                ts=checkpoint_dict.get("ts", datetime.now().isoformat()),
                id=checkpoint_id,
                channel_values={
                    **checkpoint_dict.get("channel_values", {}),
                    "messages": final_messages
                },
                channel_versions=checkpoint_dict.get("channel_versions", {}),
                versions_seen=checkpoint_dict.get("versions_seen", {})
            )

            # 确保元数据包含必要字段
            metadata = memory_tuple.metadata.copy() if memory_tuple.metadata else {}
            if "step" not in metadata:
                metadata["step"] = 0

            # 更新 config
            updated_config = config.copy()
            updated_config.setdefault("configurable", {})["checkpoint_id"] = checkpoint_id

            return CheckpointTuple(
                config=updated_config,
                checkpoint=checkpoint,
                metadata=metadata,
                parent_config=memory_tuple.parent_config,
                pending_writes=memory_tuple.pending_writes or []
            )

        # 如果没有内存检查点，但有历史消息
        if messages:
            checkpoint_id = self._generate_checkpoint_id()
            checkpoint = Checkpoint(
                v=1,
                ts=datetime.now().isoformat(),
                id=checkpoint_id,
                channel_values={"messages": messages},
                channel_versions={},
                versions_seen={}
            )

            # 创建包含必要字段的元数据
            metadata = {
                "step": 0,
                "source": "input"
            }

            # 更新 config
            updated_config = config.copy()
            updated_config.setdefault("configurable", {})["checkpoint_id"] = checkpoint_id

            return CheckpointTuple(
                config=updated_config,
                checkpoint=checkpoint,
                metadata=metadata,
                parent_config=None,
                pending_writes=[]
            )

        return None

    async def aput(self, config, checkpoint, metadata, new_versions):
        """异步保存检查点"""
        # 从 config 中获取 user_id
        user_id = self._get_user_id_from_config(config)

        # 先保存到内存
        saved_config = await self._memory_saver.aput(config, checkpoint, metadata, new_versions)

        # 提取消息并同步到 Redis
        channel_values = checkpoint.get("channel_values", {})
        if "messages" in channel_values:
            messages = channel_values["messages"]
            # 验证消息完整性
            messages = self._validate_and_fix_messages(messages)

            try:
                # 完全替换 Redis 中的消息
                await self.redis_client.async_clear_message_queue(user_id)
                # 写入所有消息
                for msg in messages:
                    await self.redis_client.async_add_message_to_queue(
                        user_id, msg, self.max_length
                    )
            except Exception as e:
                print(f"同步消息到Redis失败: {e}")

        return saved_config

    async def aput_writes(self, config, writes, task_id, task_path=""):
        """异步保存中间写入"""
        await self._memory_saver.aput_writes(config, writes, task_id, task_path)
        # 注意！！！！！！！！！：中间写入可能不完整，不应该立即写入 Redis
        # 应该在 aput() 方法中写入完整的消息列表


def create_test_tools():
    """创建测试工具"""

    def get_weather(city: str) -> str:
        """获取城市天气信息"""
        weather_data = {
            "北京": "晴天，温度 20°C",
            "上海": "多云，温度 18°C",
            "广州": "小雨，温度 22°C"
        }
        return weather_data.get(city, f"{city}的天气信息暂时不可用")

    def calculate(expression: str) -> str:
        """计算数学表达式"""
        try:
            result = eval(expression, {"__builtins__": {}}, {})
            return f"计算结果: {result}"
        except Exception as e:
            return f"计算错误: {str(e)}"

    tools = [
        Tool(
            name="get_weather",
            func=get_weather,
            description="获取指定城市的天气信息。输入应该是城市名称，例如：北京、上海、广州"
        ),
        Tool(
            name="calculate",
            func=calculate,
            description="计算数学表达式。输入应该是数学表达式，例如：2+2, 10*5, 100/4"
        )
    ]

    return tools


async def example_usage():
    redis = AsyncRedisClient()
    tools = create_test_tools()
    llm = ChatOpenAI(
        base_url="https://globalai.vip/v1",
        api_key="sk-WXTH7BshmjS9BITfMYZMA36dnyxtir8guFeuMXLGuZTnJe5Q",
        model="gpt-4o",
        temperature=0
    )

    user_id = "1008614"

    # 不再需要传入 user_id，checkpointer 会自动从 config 中读取
    some_checkpointer = CustomRedisCheckpointAdapter(
        redis_client=redis
    )

    # 创建 Agent
    agent = create_agent(llm, tools=tools, checkpointer=some_checkpointer)

    # 准备 config（必须包含 thread_id）
    # checkpointer 会自动从 config 中的 thread_id 获取 user_id
    config = {
        "configurable": {
            "thread_id": user_id
        }
    }

    # 调用 Agent
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content="草泥马")]},
        config=config
    )

    print("Agent 执行结果:")
    if "messages" in result:
        for msg in result["messages"]:
            if hasattr(msg, "content"):
                print(f"  {type(msg).__name__}: {msg.content}")
    else:
        print(result)

    # 查看写入的消息
    print("\n从 Redis 读取的消息:")
    all_messages = await redis.async_get_message_queue(user_id)
    for i, msg in enumerate(all_messages, 1):
        print(f"{i}. [{type(msg).__name__}] {msg.content}")


if __name__ == "__main__":
    asyncio.run(example_usage())