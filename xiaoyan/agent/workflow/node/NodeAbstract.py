# 抽象节点类
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

T = TypeVar('T')


class NodeAbstract(ABC, Generic[T]):

    @abstractmethod
    def run_node(self, input_data: T, **kwargs) -> str:
        pass
