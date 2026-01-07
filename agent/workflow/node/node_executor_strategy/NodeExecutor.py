from abc import ABC, abstractmethod
from typing import Any, Dict


# ============ 执行器基类 ============
class NodeExecutor(ABC):
    """节点执行器基类"""

    @abstractmethod
    async def execute(self, input_data: Any, config: Any) -> Any:
        """执行节点逻辑"""
        pass
