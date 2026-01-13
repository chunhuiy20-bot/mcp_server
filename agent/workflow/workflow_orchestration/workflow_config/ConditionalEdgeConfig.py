from dataclasses import dataclass, field
from typing import Dict
from langgraph.graph import END
from agent.workflow.workflow_orchestration.workflow_config.EdgeConfig import EdgeConfig
from agent.workflow.workflow_orchestration.workflow_config.EdgeType import EdgeType


@dataclass
class ConditionalEdgeConfig(EdgeConfig):
    """条件边配置"""
    edge_type: EdgeType = EdgeType.CONDITIONAL
    condition_field: str = ""  # 状态中用于判断的字段
    condition_map: Dict[str, str] = field(default_factory=dict)  # 值 -> 目标节点映射
    default_target: str = END  # 默认目标
