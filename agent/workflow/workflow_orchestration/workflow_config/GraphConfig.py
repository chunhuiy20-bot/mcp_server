
from dataclasses import dataclass
from typing import Dict, Any, List


# ============ 图配置 ============
@dataclass
class GraphConfig:
    """图配置"""
    name: str
    state_schema: Dict[str, Any]  # 状态 schema
    nodes: List[Dict[str, Any]]  # 节点配置列表
    edges: List[Dict[str, Any]]  # 边配置列表
    entry_point: str  # 入口节点
    description: str = ""
