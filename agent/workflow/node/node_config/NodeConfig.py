from dataclasses import dataclass
from typing import Optional
from agent.workflow.node.node_config.CodeConfig import CodeConfig
from agent.workflow.node.node_config.LLMConfig import LLMConfig


@dataclass
class NodeConfig:
    """节点配置类"""
    node_name: str
    node_config: Optional[LLMConfig | CodeConfig] = None  # llm | code
