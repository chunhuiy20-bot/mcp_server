from dataclasses import dataclass, field
from typing import List
import os
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from agent.ai_chat.AIChatAbstract import AIChatAbstract
from agent.react_agent.EnhanceTool import EnhanceTool

load_dotenv()


@dataclass
class MCPConfig:
    server_name: str
    server_url: str
    transport: str
    # 是否必要，如果必要,但是却无法获取到服务器就会创建失败
    is_necessary: bool = False


@dataclass
class LLMConfig:
    openai_api_key: str = field(default=os.getenv("OPENAI_API_KEY"))
    openai_api_base: str = field(default=os.getenv("OPENAI_API_BASE"))
    model: str = field(default="gpt-4.1")
    temperature: float = field(default=0.0)


@dataclass
class MemoryConfig:
    enable_memory: bool = field(default=False)
    memory_type: str = field(default="MemorySaver")
    max_history_limit: int = field(default=100)


@dataclass
class ReactAgentConfig:
    agent_name: str = "ReactAgent"
    system_prompt: str = "你是一个AI助手"
    llm_config: LLMConfig = field(default_factory=LLMConfig)
    mcp_configs: List[MCPConfig] = field(default_factory=list)
    memory_config: MemoryConfig = field(default_factory=MemoryConfig)


class ReactAgent(AIChatAbstract):
    def __init__(self, config: ReactAgentConfig, user_id: str):
        self.config = config
        self.user_id = user_id  # 每个实例绑定一个用户ID
        self.mcp_client = None
        self._raw_tools = []
        self._initialized = False

        self._enhanced_tools = None  # 缓存增强工具
        self._agent = None  # 缓存agent实例
        self._cache_enabled = True  # 缓存开关

        # 初始化记忆组件
        self.checkpointer = self._init_memory()

    async def chat(self, user_input: str, **kwargs):
        """聊天方法 - 不需要传user_id了"""
        agent = await self._get_agent()
        _checkpointer_config = None
        if self.checkpointer is not None:
            if unique_identifier := kwargs.get("unique_identifier"):
                _checkpointer_config = await self._get_checkpointer_config(unique_identifier)
            else:
                _checkpointer_config = await self._get_checkpointer_config(self.user_id)
        user_input_dict = await self._bulid_user_input(user_input, **kwargs)
        res = await agent.ainvoke(input=user_input_dict, config=_checkpointer_config)
        return res["messages"][-1].content

    async def chat_stream(self, user_input: str, **kwargs):
        """流式聊天方法"""
        agent = await self._get_agent()
        async for chunk in agent.astream({"messages": [{"role": "user", "content": user_input}]}):
            yield chunk

    async def update_config(self, new_config: ReactAgentConfig):
        """更新配置，如果有变化则重新加载工具"""
        if new_config == self.config:
            print(f"用户 {self.user_id} - 配置未改变，无需重新加载工具")
            return
        else:
            print(f"用户 {self.user_id} - 配置已改变，重新加载工具...")
            self.config = new_config
            await self._reload_tools()

    # todo “User Bio” and “Model Set Context” 用户个性化
    async def call_msc(self):
        pass

    # noinspection PyMethodMayBeStatic
    async def _bulid_user_input(self, user_input: str, **kwargs):
        image_list = kwargs.get("image_list", [])
        # 如果没有图片，返回简单的文本消息
        if not image_list or len(image_list) == 0:
            return {"messages": [{"role": "user", "content": user_input}]}
        content = [
            {"type": "text", "text": user_input}
        ]
        for image_url in image_list:
            content.append({
                "type": "image_url",
                "image_url": {"url": image_url}
            })

        return {"messages": [{"role": "user", "content": content}]}



    def _init_memory(self):
        """初始化记忆组件"""
        if not self.config.memory_config.enable_memory:
            print(f"用户 {self.user_id} - 记忆功能已禁用")
            return None

        memory_type = self.config.memory_config.memory_type

        if memory_type == "MemorySaver":
            checkpointer = MemorySaver()
            print(f"用户 {self.user_id} - 使用内存记忆 (MemorySaver)")
        else:
            print(f"用户 {self.user_id} - 未知的记忆类型 {memory_type}，使用默认内存记忆")
            checkpointer = MemorySaver()
        return checkpointer

    # noinspection PyMethodMayBeStatic
    async def _get_checkpointer_config(self, unique_identifier: str):
        """获取记忆组件的配置"""
        if unique_identifier is None:
            return None
        checkpointer_config = {"configurable": {"thread_id": unique_identifier}}
        return checkpointer_config

    async def _ensure_initialized(self):
        """确保基础初始化完成"""
        if not self._initialized:
            await self._init_raw_mcp()
            self._initialized = True

    async def _get_enhanced_tools(self):
        """获取增强工具（带缓存）"""
        await self._ensure_initialized()

        # 检查缓存
        if self._cache_enabled and self._enhanced_tools is not None:
            print(f"从缓存获取用户 {self.user_id} 的工具")
            return self._enhanced_tools

        # 创建新增强工具
        enhanced_tools = []
        for tool in self._raw_tools:
            enhanced_tool = EnhanceTool(tool, self.user_id)
            enhanced_tools.append(enhanced_tool)

        # 缓存工具
        if self._cache_enabled:
            self._enhanced_tools = enhanced_tools
            print(f"为用户 {self.user_id} 创建并缓存了 {len(enhanced_tools)} 个工具")

        return enhanced_tools

    async def _get_agent(self):
        """获取agent实例（带缓存）"""
        # 检查缓存
        if self._cache_enabled and self._agent is not None:
            print(f"从缓存获取用户 {self.user_id} 的agent")
            return self._agent

        # 创建新的agent
        tools = await self._get_enhanced_tools()

        agent = create_agent(
            name=self.config.agent_name,
            system_prompt=self.config.system_prompt,   # todo 这个最好不要固定，而是使用动态增强
            model=ChatOpenAI(
                model=self.config.llm_config.model,
                temperature=self.config.llm_config.temperature,
                api_key=self.config.llm_config.openai_api_key,
                base_url=self.config.llm_config.openai_api_base
            ),
            tools=tools,
            checkpointer=self.checkpointer
        )

        # 缓存agent
        if self._cache_enabled:
            self._agent = agent
            print(f"为用户 {self.user_id} 创建并缓存了agent")

        return agent

    def _clear_cache(self):
        """清理缓存"""
        self._enhanced_tools = None
        self._agent = None
        print(f"已清理用户 {self.user_id} 的缓存")

    async def _init_raw_mcp(self):
        """初始化MCP客户端并加载工具"""
        if not self.config.mcp_configs or len(self.config.mcp_configs) == 0:
            return []

        # 构建服务器配置
        mcp_servers = {}
        for mcp_config in self.config.mcp_configs:
            mcp_servers[mcp_config.server_name] = {
                "transport": mcp_config.transport,
                "url": mcp_config.server_url
            }

        try:
            # 创建MCP客户端
            self.mcp_client = MultiServerMCPClient(mcp_servers)
            print(f"用户 {self.user_id} - MCP客户端初始化完成，共 {len(mcp_servers)} 个服务器")

            # 从每个服务器加载工具
            for mcp_config in self.config.mcp_configs:
                server_name = mcp_config.server_name
                try:
                    # 加载工具
                    raw_tools = await self.mcp_client.get_tools(server_name=server_name)
                    print(f"用户 {self.user_id} - 从 {server_name}加载了 {len(raw_tools)} 个工具")
                    for tool in raw_tools:
                        self._raw_tools.append(tool)
                except Exception as e:
                    print(f"用户 {self.user_id} - 从 {server_name} 加载工具失败:{e}")
                    if mcp_config.is_necessary:
                        raise e
                    else:
                        continue

            print(f"用户 {self.user_id} - 总共加载了 {len(self._raw_tools)} 个工具")
            return self._raw_tools

        except Exception as e:
            print(f"用户 {self.user_id} - MCP客户端初始化失败:{e}")
            return []

    async def _reload_tools(self):
        """重新加载工具"""
        print(f"用户 {self.user_id} - 重新加载工具，清理缓存...")
        self._initialized = False
        self._raw_tools.clear()
        self._clear_cache()
        await self._ensure_initialized()


class ReactAgentBuilder:
    def __init__(self, agent_name: str):
        self._config = ReactAgentConfig(agent_name=agent_name)

    def with_system_prompt(self, prompt: str):
        self._config.system_prompt = prompt
        return self

    def with_llm_config(self, llm_config: LLMConfig):
        self._config.llm_config = llm_config
        return self

    def with_mcp_config(self, mcp_config: MCPConfig):
        self._config.mcp_configs.append(mcp_config)
        return self

    def with_memory_config(self, memory_config: MemoryConfig):
        self._config.memory_config = memory_config
        return self

    async def build(self, user_id: str):  # 现在需要传入user_id
        return ReactAgent(self._config, user_id)


async def main():
    react_agent = (await ReactAgentBuilder(agent_name="test_agent")
                   .with_memory_config(MemoryConfig(enable_memory=True))
                   .with_llm_config(LLMConfig())
                   .with_system_prompt("你是一个助手。如果有必要，请有序调用方法。如果有网络搜索的消息请包涵信息来源，以markdown格式回复，如果有未知的信息可以先进行长期记忆查找。")
                   .with_mcp_config(MCPConfig(server_name="WebSearchMCP", server_url="http://localhost:8001/mcp", transport="http", is_necessary=True))
                   .with_mcp_config(MCPConfig(server_name="ImageMCP", server_url="http://localhost:8002/mcp", transport="http", is_necessary=True))
                   .with_mcp_config(MCPConfig(server_name="DocumentMCP", server_url="http://localhost:8003/mcp", transport="http", is_necessary=True))
                    .with_mcp_config(MCPConfig(server_name="LongMemoryMCP", server_url="http://localhost:8004/mcp", transport="http", is_necessary=True))
                   .build("1008611"))

    # print(await react_agent.chat(user_input="这两张图片是什么",
    #                              image_list=["https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTPq1dP1m4_7I-yGmGHxnyMmtgVLE9EB_PUiQ&s","https://rimage.gnst.jp/livejapan.com/public/article/detail/a/00/00/a0000276/img/basic/a0000276_main.jpg"]))
    #
    # print(await react_agent.chat("那这张呢？这个道题的答案是什么", image_list=["https://blog.amazingtalker.com/wp-content/uploads/2022/09/%E4%BB%A3%E5%85%A5%E6%B6%88%E5%8E%BB%E6%B3%95.png"]))

    # print(await react_agent.chat("BTC市场情绪怎么样"))
    # print(await react_agent.chat("查询一下今天的热点新闻，然后根据情况生成一些合适的图片，并给我整理成一个文档，我要用来做自媒体的稿子，图片地址要完整后面接的参数不能少，否则是无法访问的，md格式"))
    # print(await react_agent.chat("我当前文件夹下有什么，读取一下md文件，告诉我他写了什么"))

    print(await react_agent.chat("我的好朋友有谁"))
    # print(await react_agent.chat("我之前给过你”"))
    # print(await react_agent.chat("你调用工具查呀”"))




if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
