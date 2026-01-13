import asyncio
import json
from datetime import datetime
from typing import Any, Optional, Iterator, Sequence
from concurrent.futures import ThreadPoolExecutor
import uuid
from pathlib import Path
from langchain.agents import create_agent
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, BaseMessage, AIMessage, ToolMessage
from langgraph.checkpoint.base import BaseCheckpointSaver, CheckpointTuple
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import Checkpoint, CheckpointMetadata, ChannelVersions
from agent.memory.custom.redis.RedisClient import AsyncRedisClient


# noinspection PyMethodMayBeStatic
class CustomRedisCheckpointAdapter(BaseCheckpointSaver):
    """
    基于Langgraph的抽象类BaseCheckpointSaver和redis实现自定义检查点适配
    核心功能：基于Langgraph的抽象类BaseCheckpointSaver实现自定义的检测点，抛弃Langgraph框架内置检查点的信息冗余，轻量化存储【牺牲会话中断恢复能力，如果需要请使用框架内置的检查点】。
            1、get_tuple / aget_tuple 方法：读取检查点（恢复上次会话状态）。
                1、由于主要是异步编程，所以主要在aget_tuple方法中，这个方法会根据RunnableConfig中配置唯一字段查询redis中的历史消息
                2、同时验证消息完整性，（处理 tool_calls 配对问题，因为大模型处理工具调用的时候，工具调用信息必须配对）
                3、当Langgraph启动的时候，这个方法会被率先调用,恢复之前的对话状态。
            2、put/aput  保存检查点（持久化状态）
                1、同理，主要用aput方法
                2、在Langgraph的框架中，每次节点执行完，LangGraph 调用这个方法保存状态。
                   这个方法被调用的情况风两种:
                        2.1、 ReActAgent作为独立的LangGraph图的时候(ReActAgent本身是用LangGraph构建),那么调用工具(mcp)返回的值也会被加入历史消息
                        2.2、 ReAct Agent 作为你工作流的一个节点，那么中间值不会被加入历史消息
                        本质上，只要 channel_values["messages"] 里有消息，就会保存。所以:
                        如果 ReAct Agent 把 ToolMessage 放进了 messages，就会保存
                        如果 ReAct Agent 只返回最终的 AIMessage，工具调用过程就不会保存
               3、重新实现的变化:
                    跳过中间状态，只保存最终状态,增量添加，避免重复,超出长度的旧消息保存到文件(可选)

            3、put_writes / aput_writes
                重新实现的变化: 不加入中间状态，只保持最终状态，使得消息队列不臃肿
            4、list 列出历史检查点
                重新实现的主要修改： 列出检查点(简化原来的,只返回当前消息队列的检查点）
            5、_validate_and_fix_messages 方法
                核心功能：历史消息完整性验证
                1、确保每个带 tool_calls 的 AIMessage 都有对应的 ToolMessage。如果不完整，移除这些消息，避免 LangGraph 报错，导致运行中断
    """


    def __init__(self, redis_client: AsyncRedisClient, max_length: int = 1000, save_exceeding_message_to_file: bool = False):
        super().__init__()
        self.redis_client: AsyncRedisClient = redis_client
        self.max_length = max_length
        # 创建线程池用于执行异步操作
        self._executor = ThreadPoolExecutor(max_workers=1)
        self.save_exceeding_message_to_file = save_exceeding_message_to_file

    def _get_user_id_from_config(self, config: RunnableConfig) -> str:
        """从 config 中获取 user_id（即 thread_id）"""
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            raise ValueError("config 中必须包含 'configurable.thread_id'")
        return str(thread_id)

    def _run_async(self, coro):
        """在同步方法中运行异步函数"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                future = self._executor.submit(asyncio.run, coro)
                return future.result()
            else:
                return loop.run_until_complete(coro)
        except RuntimeError:
            return asyncio.run(coro)

    def _generate_checkpoint_id(self) -> str:
        """生成有效的 UUID 格式的 checkpoint ID"""
        return str(uuid.uuid4())

    def _validate_and_fix_messages(self, messages: list[BaseMessage]) -> list[BaseMessage]:
        """
        验证并修复消息列表的完整性
        核心功能: 确保每个包含 tool_calls 的 AIMessage 都有对应的 ToolMessage
        """
        if not messages:
            return messages

        validated_messages = []
        pending_tool_calls = {}  # {tool_call_id: AIMessage}

        for msg in messages:
            if isinstance(msg, AIMessage):
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        tool_call_id = tool_call.get('id') if isinstance(tool_call, dict) else getattr(tool_call, 'id', None)
                        if tool_call_id:
                            pending_tool_calls[tool_call_id] = msg
                    validated_messages.append(msg)
                else:
                    if pending_tool_calls:
                        validated_messages = [m for m in validated_messages
                                              if not (isinstance(m, AIMessage) and
                                                      hasattr(m, 'tool_calls') and m.tool_calls)]
                        pending_tool_calls.clear()
                    validated_messages.append(msg)

            elif isinstance(msg, ToolMessage):
                tool_call_id = getattr(msg, 'tool_call_id', None)
                if tool_call_id and tool_call_id in pending_tool_calls:
                    del pending_tool_calls[tool_call_id]
                    validated_messages.append(msg)
                elif tool_call_id:
                    continue
                else:
                    validated_messages.append(msg)

            else:
                if pending_tool_calls:
                    validated_messages = [m for m in validated_messages
                                          if not (isinstance(m, AIMessage) and
                                                  hasattr(m, 'tool_calls') and m.tool_calls)]
                    pending_tool_calls.clear()
                validated_messages.append(msg)

        if pending_tool_calls:
            validated_messages = [m for m in validated_messages
                                  if not (isinstance(m, AIMessage) and
                                          hasattr(m, 'tool_calls') and m.tool_calls)]

        return validated_messages

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """同步获取检查点"""
        return self._run_async(self.aget_tuple(config))

    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """异步获取检查点 - 直接从 Redis 消息队列读取"""
        # 1. 从 config 获取 user_id（即 thread_id）
        user_id = self._get_user_id_from_config(config)

        #  2. 从 Redis 消息队列读取历史消息
        try:
            messages = await self.redis_client.async_get_message_queue(user_id)
            # 3. 验证消息完整性（处理 tool_calls 配对问题）
            messages = self._validate_and_fix_messages(messages)
        except Exception as e:
            print(f"读取历史消息失败: {e}")
            messages = []

        # 4. 如果没有消息，返回 None（LangGraph 会创建新状态）
        if not messages:
            return None

        # 5. 构建 Checkpoint 对象
        checkpoint_id = self._generate_checkpoint_id()
        checkpoint = Checkpoint(
            v=1,
            ts=datetime.now().isoformat(),
            id=checkpoint_id,
            channel_values={"messages": messages},
            channel_versions={},
            versions_seen={}
        )

        # 创建元数据
        metadata = CheckpointMetadata(
            step=0,
            source="input"
        )

        # 更新 config
        updated_config = config.copy()
        updated_config.setdefault("configurable", {})["checkpoint_id"] = checkpoint_id

        # 6. 返回 CheckpointTuple
        return CheckpointTuple(
            config=updated_config,
            checkpoint=checkpoint,
            metadata=metadata,
            parent_config=None,
            pending_writes=[]
        )

    def put(
            self,
            config: RunnableConfig,
            checkpoint: Checkpoint,
            metadata: CheckpointMetadata,
            new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """同步保存检查点"""
        return self._run_async(self.aput(config, checkpoint, metadata, new_versions))

    async def aput(
            self,
            config: RunnableConfig,
            checkpoint: Checkpoint,
            metadata: CheckpointMetadata,
            new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """
        最终状态才写入，这样可以减少io开销
        异步保存检查点 - 直接保存到 Redis 消息队列
        """
        user_id = self._get_user_id_from_config(config)

        # 提取消息
        channel_values = checkpoint.get("channel_values", {})

        # 1. 过滤中间状态（只保存最终状态，减少 IO）
        if "__start__" in channel_values:
            # 这是初始状态，不写入
            # print(f"初始状态:{channel_values}")
            checkpoint_id = checkpoint.get("id") or self._generate_checkpoint_id()
            updated_config = config.copy()
            updated_config.setdefault("configurable", {})["checkpoint_id"] = checkpoint_id
            return updated_config

        # 检查是否有 branch: 开头的 key（中间路由状态）
        has_branch_keys = any(key.startswith("branch:") for key in channel_values.keys())
        if has_branch_keys:
            # print(f"中间路由状态:{channel_values}")
            # 这是中间路由状态，不写入
            checkpoint_id = checkpoint.get("id") or self._generate_checkpoint_id()
            updated_config = config.copy()
            updated_config.setdefault("configurable", {})["checkpoint_id"] = checkpoint_id
            return updated_config

        # 2. 只处理包含 messages 的最终状态
        if "messages" in channel_values:
            new_messages = channel_values["messages"]
            # 验证并修复消息完整性
            new_messages = self._validate_and_fix_messages(new_messages)
            # print(f"收到的所有消息: {new_messages}")  # 添加这行调试
            # print(f"消息类型: {[type(m).__name__ for m in new_messages]}")  # 添加这行
            try:
                # 3. 增量添加：从 Redis 读取当前消息列表，然后增量添加
                existing_messages = await self.redis_client.async_get_message_queue(user_id)

                # 获取现有消息的 ID 集合（用于去重）
                existing_message_ids = set()
                for msg in existing_messages:
                    msg_id = getattr(msg, 'id', None)
                    if msg_id:
                        existing_message_ids.add(msg_id)

                # 找出需要添加的新消息（通过消息 ID 判断）
                messages_to_add = []
                for msg in new_messages:
                    msg_id = getattr(msg, 'id', None)
                    # 如果消息没有 ID，或者 ID 不在现有消息中，则认为是新消息
                    if not msg_id or msg_id not in existing_message_ids:
                        messages_to_add.append(msg)
                        if msg_id:
                            existing_message_ids.add(msg_id)  # 避免重复添加
                print(f"需要添加的新消息:{messages_to_add}")
                # 增量添加新消息
                if messages_to_add:
                    for msg in messages_to_add:
                        out_limit, deleted_list = await self.redis_client.async_add_message_to_queue(
                            user_id, msg, self.max_length
                        )
                        print(f"消息队列已满，已删除部分消息:{len(deleted_list)} - {deleted_list}")
                        if deleted_list and self.save_exceeding_message_to_file:
                            # 异步处理被移除的消息，不阻塞主流程
                            asyncio.create_task(
                                self._process_removed_messages(deleted_list, user_id)
                            )

            except Exception as e:
                print(f"增量添加消息到Redis失败: {e}")

        # 更新 config（生成新的 checkpoint_id）
        checkpoint_id = checkpoint.get("id") or self._generate_checkpoint_id()
        updated_config = config.copy()
        updated_config.setdefault("configurable", {})["checkpoint_id"] = checkpoint_id

        return updated_config

    async def _process_removed_messages(self, removed_messages: list[BaseMessage], user_id: str):
        """
        异步处理被移除的消息
        将完整的会话（用户提问 + AI回复）保存到文档，每个会话占一行
        """
        try:
            if not removed_messages:
                return

            # 将消息组织成会话（HumanMessage + AIMessage + 可能的 ToolMessage）
            sessions = self._organize_messages_into_sessions(removed_messages)

            if not sessions:
                return

            # 获取存储目录（可以根据需要修改路径）
            storage_dir = Path("user_memory")
            storage_dir.mkdir(exist_ok=True)

            # 为每个用户创建单独的文件
            file_path = storage_dir / f"{user_id}.txt"

            # 异步写入文件（使用 aiofiles 或同步写入，因为文件操作通常很快）
            # 如果文件很大，可以考虑使用 aiofiles
            with open(file_path, 'a', encoding='utf-8') as f:
                for session in sessions:
                    # 每个会话占一行，使用 JSON 格式
                    session_data = {
                        "timestamp": datetime.now().isoformat(),
                        "user_id": user_id,
                        "messages": [
                            {
                                "type": type(msg).__name__,
                                "content": getattr(msg, 'content', ''),
                                "id": getattr(msg, 'id', None)
                            }
                            for msg in session
                        ]
                    }
                    f.write(json.dumps(session_data, ensure_ascii=False) + '\n')

            print(f"已保存 {len(sessions)} 个会话到 {file_path}")

        except Exception as e:
            print(f"处理被移除消息时出错: {e}")

    def _organize_messages_into_sessions(self, messages: list[BaseMessage]) -> list[list[BaseMessage]]:
        """
        将消息组织成完整的会话
        一个会话 = HumanMessage + (ToolMessage*) + AIMessage
        """
        sessions = []
        current_session = []

        for msg in messages:
            if isinstance(msg, HumanMessage):
                # 如果遇到新的 HumanMessage，且当前会话不为空，保存上一个会话
                if current_session:
                    sessions.append(current_session)
                # 开始新会话
                current_session = [msg]

            elif isinstance(msg, (AIMessage, ToolMessage)):
                # AI 回复或工具调用，添加到当前会话
                current_session.append(msg)

                # 如果是 AIMessage 且没有待处理的 tool_calls，会话结束
                if isinstance(msg, AIMessage):
                    has_tool_calls = hasattr(msg, 'tool_calls') and msg.tool_calls
                    if not has_tool_calls:
                        # 会话完整，保存
                        sessions.append(current_session)
                        current_session = []

            else:
                # 其他类型的消息，添加到当前会话
                current_session.append(msg)

        # 保存最后一个会话（如果有）
        if current_session:
            sessions.append(current_session)

        return sessions

    @staticmethod
    async def _process_removed_messages_static(removed_messages: list[BaseMessage], user_id: str):
        """
        静态方法处理，不依赖实例
        根据id创建一个文档，removed_messages一定是一个会话（即用户提问--ai完整回复），每个removed_messages占一行
        """
        try:
            if not removed_messages:
                return

            # 获取存储目录
            storage_dir = Path("removed_messages")
            storage_dir.mkdir(exist_ok=True)

            # 为每个用户创建单独的文件
            file_path = storage_dir / f"{user_id}.txt"

            # 组织会话数据
            session_data = {
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "messages": [
                    {
                        "type": type(msg).__name__,
                        "content": getattr(msg, 'content', ''),
                        "id": getattr(msg, 'id', None)
                    }
                    for msg in removed_messages
                ]
            }

            # 追加写入文件
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(session_data, ensure_ascii=False) + '\n')

            print(f"{user_id} 已保存被移除的会话到 {file_path}")

        except Exception as e:
            print(f"处理被移除消息时出错: {e}")

    def put_writes(
            self,
            config: RunnableConfig,
            writes: Sequence[tuple[str, Any]],
            task_id: str,
            task_path: str = "",
    ) -> None:
        """同步保存中间写入（暂不实现，等待完整检查点）"""
        # 中间写入不立即保存，等待完整检查点
        pass

    async def aput_writes(
            self,
            config: RunnableConfig,
            writes: Sequence[tuple[str, Any]],
            task_id: str,
            task_path: str = "",
    ) -> None:
        """异步保存中间写入（暂不实现，等待完整检查点）"""
        # 中间写入不立即保存，等待完整检查点
        pass

    def list(
            self,
            config: RunnableConfig,
            *,
            filter: Optional[dict] = None,
            before: Optional[str] = None,
            limit: Optional[int] = None
    ) -> Iterator[CheckpointTuple]:
        """列出检查点（简化版本，只返回当前消息队列的检查点）"""
        # 由于只使用消息队列，无法列出历史检查点
        # 只返回当前检查点（如果有）
        tuple_result = self.get_tuple(config)
        if tuple_result:
            yield tuple_result


# 测试工具和示例代码保持不变
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

    # 完全基于 Redis 消息队列的检查点适配器
    checkpointer = CustomRedisCheckpointAdapter(
        redis_client=redis
    )

    # 创建 Agent
    agent = create_agent(llm, tools=tools, checkpointer=checkpointer)

    # 准备 config
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
