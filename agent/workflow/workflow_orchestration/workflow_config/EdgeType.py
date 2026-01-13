from enum import Enum


# ============ 边配置 ============
class EdgeType(Enum):
    NORMAL = "normal"  # 普通边
    CONDITIONAL = "conditional"  # 条件边
