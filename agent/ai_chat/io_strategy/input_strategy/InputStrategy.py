from abc import ABC, abstractmethod
from typing import Any

from schemas.common.Result import Result


class InputStrategy(ABC):
    """输入处理策略接口"""

    @abstractmethod
    async def process(self, data: Any, **kwargs) -> Result[str]:
        """将输入转换为文本"""
        pass
