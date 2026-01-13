from dataclasses import dataclass
from agent.workflow.workflow_orchestration.workflow_config.EdgeType import EdgeType


@dataclass
class EdgeConfig:
    """边配置"""
    source: str  # 源节点名称
    target: str  # 目标节点名称 (普通边)
    edge_type: EdgeType = EdgeType.NORMAL
    