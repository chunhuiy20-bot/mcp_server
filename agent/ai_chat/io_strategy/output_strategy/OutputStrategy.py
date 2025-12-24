from abc import ABC, abstractmethod
from typing import Any


class OutputStrategy(ABC):
    """输出处理策略接口"""

    @abstractmethod
    async def process(self, text: str) -> Any:
        """将文本转换为目标格式"""
        pass
