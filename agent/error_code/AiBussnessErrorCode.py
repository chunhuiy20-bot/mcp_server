from enum import Enum
from typing import Optional, Any


class AIBusinessErrorCode(Enum):
    """业务错误码"""

    # 输入策略错误 2xxx
    UNSUPPORTED_INPUT_TYPE = (20001, "不支持的输入类型")
    INPUT_PROCESS_FAILED = (20002, "输入处理失败")

    # 输出策略错误 3xxx
    UNSUPPORTED_OUTPUT_TYPE = (30001, "不支持的输出类型")
    OUTPUT_PROCESS_FAILED = (30002, "输出处理失败")

    # AI智能体错误 4xxx
    AGENT_INIT_FAILED = (40001, "智能体初始化失败")
    AGENT_CALL_FAILED = (40002, "智能体调用失败")

    # MCP服务错误 5xxx
    MCP_CONNECTION_FAILED = (50001, "MCP服务连接失败")
    MCP_TOOL_LOAD_FAILED = (50002, "MCP工具加载失败")

    # workflow 编排错误 6xxx
    WORKFLOW_CONFIG_ERROR = (60001, "工作流配置错误")

    # checkpointer 配置错误 7xxx
    MONGODB_CHECKPOINTER_CONNECT_ERROR = (70001, "mongodb检查点配置错误")

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message