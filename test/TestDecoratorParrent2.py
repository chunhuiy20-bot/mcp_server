from typing import List, Dict, Callable, Optional
from dataclasses import dataclass, field


# 策略接口
class MCPTool:
    def execute(self, *args, **kwargs):
        raise NotImplementedError


# 具体MCP工具
class SearchTool(MCPTool):
    def execute(self, query: str):
        return f"搜索结果: {query}"


class CodeAnalysisTool(MCPTool):
    def execute(self, code: str):
        return f"分析代码: {code}"


class DatabaseTool(MCPTool):
    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def execute(self, query: str):
        return f"执行SQL: {query}"


# 智能体配置
@dataclass
class AgentConfig:
    user_id: str
    system_prompt: str = "你是一个AI助手"
    temperature: float = 0.7
    max_tokens: int = 2000
    mcp_tools: List[MCPTool] = field(default_factory=list)
    custom_instructions: List[str] = field(default_factory=list)
    memory_enabled: bool = True
    metadata: Dict = field(default_factory=dict)


# 智能体类
class Agent:
    def __init__(self, config: AgentConfig):
        self.config = config

    def process(self, user_input: str) -> str:
        # 构建完整提示词
        full_prompt = self._build_prompt(user_input)
        print("full:"+full_prompt)
        # 执行工具
        tool_results = []
        for tool in self.config.mcp_tools:
            # 这里简化了工具调用逻辑
            pass

        return f"处理用户 {self.config.user_id} 的请求: {user_input}"

    def _build_prompt(self, user_input: str) -> str:
        parts = [self.config.system_prompt]
        parts.extend(self.config.custom_instructions)
        parts.append(f"用户输入: {user_input}")
        return "\n".join(parts)


# 建造者模式
class AgentBuilder:
    def __init__(self, user_id: str):
        self._config = AgentConfig(user_id=user_id)

    def with_system_prompt(self, prompt: str):
        self._config.system_prompt = prompt
        return self

    def with_temperature(self, temp: float):
        self._config.temperature = temp
        return self

    def with_max_tokens(self, tokens: int):
        self._config.max_tokens = tokens
        return self

    def add_mcp_tool(self, tool: MCPTool):
        self._config.mcp_tools.append(tool)
        return self

    def add_custom_instruction(self, instruction: str):
        self._config.custom_instructions.append(instruction)
        return self

    def enable_memory(self, enabled: bool = True):
        self._config.memory_enabled = enabled
        return self

    def with_metadata(self, key: str, value):
        self._config.metadata[key] = value
        return self

    def build(self) -> Agent:
        return Agent(self._config)


# 使用示例
if __name__ == "__main__":
    # 用户1: 数据分析师智能体
    analyst_agent = (AgentBuilder("user_001")
                     .with_system_prompt("你是一个专业的数据分析师")
                     .with_temperature(0.3)
                     .add_mcp_tool(DatabaseTool("postgresql://localhost"))
                     .add_mcp_tool(CodeAnalysisTool())
                     .add_custom_instruction("总是用图表展示数据")
                     .add_custom_instruction("提供详细的统计分析")
                     .with_metadata("role", "analyst")
                     .build())
    print(analyst_agent.config)

    # 用户2: 创意写作智能体
    writer_agent = (AgentBuilder("user_002")
                    .with_system_prompt("你是一个富有创意的作家")
                    .with_temperature(0.9)
                    .add_mcp_tool(SearchTool())
                    .add_custom_instruction("使用生动的比喻")
                    .add_custom_instruction("保持幽默风格")
                    .enable_memory(True)
                    .with_metadata("role", "writer")
                    .build())

    # 用户3: 技术支持智能体
    support_agent = (AgentBuilder("user_003")
                     .with_system_prompt("你是技术支持专家")
                     .with_temperature(0.5)
                     .add_mcp_tool(SearchTool())
                     .add_mcp_tool(CodeAnalysisTool())
                     .add_custom_instruction("提供分步骤的解决方案")
                     .build())

    print(analyst_agent.process("分析销售数据"))
    print(writer_agent.process("写一个科幻故事"))
    print(support_agent.process("如何修复这个bug"))
