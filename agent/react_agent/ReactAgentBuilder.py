import traceback
from dataclasses import dataclass, field
from typing import List
import os
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

@dataclass
class MCPConfig:
    server_name: str
    server_url: str
    transport: str
    # 是否必要
    is_necessary: bool = False

@dataclass
class LLMConfig:
    openai_api_key: str = field(default=os.getenv("OPENAI_API_KEY"))
    openai_api_base: str = field(default=os.getenv("OPENAI_API_BASE"))
    model:str = field(default="gpt-4.1")
    temperature: float = field(default=0.0)

@dataclass
class ReactAgentConfig:
    user_id: str  #todo  这个好像不是必须的 后面可以修改
    agent_name: str = "ReactAgent"
    system_prompt: str = "你是一个AI助手"
    llm_config: LLMConfig = field(default_factory=LLMConfig)
    mcp_configs: List[MCPConfig] = field(default_factory=list)
    enable_memory: bool = True

class ReactAgent:
    def __init__(self, config: ReactAgentConfig):
        self.config = config
        self.mcp_client = None
        self.tools = []


    async def chat_stream(self, user_input: str):
        return user_input

    async def chat(self, user_input: str):
        return user_input

    async def get_config(self):
        return self.config

    async def init_mcp(self):
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
            print(f"MCP客户端初始化完成，共 {len(mcp_servers)} 个服务器")

            # 从每个服务器加载工具
            for mcp_config in self.config.mcp_configs:
                server_name = mcp_config.server_name
                try:
                    # 加载工具
                    raw_tools = await self.mcp_client.get_tools(
                        server_name=server_name
                    )
                    print(f"从 {server_name}加载了 {len(raw_tools)} 个工具")
                    for tool in raw_tools:
                        self.tools.append(tool)

                except Exception as e:
                    print(f"从 {server_name} 加载工具失败:{e}")
                    if mcp_config.is_necessary:
                        # 必要服务器加载失败, 则停止程序
                        raise e
                    continue

            print(f"总共加载了 {len(self.tools)} 个工具")
            return self.tools

        except Exception as e:
            print(f"MCP客户端初始化失败:{e}")
            return []


class ReactAgentBuilder:
    def __init__(self, user_id: str):
        self._config = ReactAgentConfig(user_id=user_id)

    def with_agent_name(self, name: str):
        self._config.agent_name = name
        return self

    def with_system_prompt(self, prompt: str):
        self._config.system_prompt = prompt
        return self

    def with_llm_config(self, llm_config: LLMConfig):
        self._config.llm_config = llm_config
        return self

    def with_mcp_config(self, mcp_config: MCPConfig):
        self._config.mcp_configs.append(mcp_config)
        return self

    def enable_memory(self, enabled: bool = True):
        self._config.enable_memory = enabled
        return self

    async def build(self):
        return ReactAgent(self._config)



async def main():
    react_agent = (await ReactAgentBuilder(user_id="1").with_agent_name("ReactAgent")
                   .enable_memory(True).with_llm_config(LLMConfig()).
                   with_mcp_config(MCPConfig(server_name="TransactionMCP", server_url="http://localhost:8001/mcp", transport="http",is_necessary=True)).build())
    print(react_agent.tools)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())