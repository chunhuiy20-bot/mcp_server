from abc import ABC, abstractmethod
from typing import Optional, List, Type


class SQLHandlerAbstract(ABC):

    @abstractmethod
    async def execute(self, sql: Optional[str] = None, params: Optional[dict] = None):
        """
            执行SQL语句
            :param sql: SQL语句
            :param params: 参数
            :return: 结果
        """
        pass

    @abstractmethod
    async def add_one_data(self, params: Optional[dict] = None):
        """
            执行SQL语句
            :param params: 参数
            :return: 结果
        """
        pass

    @abstractmethod
    async def add_batch(self, data_list: List[dict], batch_size: Optional[int] = None):
        """批量添加数据"""
        pass

    @abstractmethod
    async def search_one_data(self, sql: Optional[str] = None, params: Optional[dict] = None, to_class: Optional[Type] = None, allow_none: bool = False):
        """
        查询一条数据
        """
        pass

    @abstractmethod
    async def search_data(self, sql: Optional[str] = None, params: Optional[dict] = None):
        """
            执行SQL语句
            :param sql: SQL语句
            :param params: 参数
            :return: 结果
        """
        pass

    @abstractmethod
    async def update_data(self, sql: Optional[str] = None, params: Optional[dict] = None):
        """
            执行SQL语句
            :param sql: SQL语句
            :param params: 参数
            :return: 结果
        """
        pass

    @abstractmethod
    async def delete_data(self, sql: Optional[str] = None, params: Optional[dict] = None):
        """
            执行SQL语句
            :param sql: SQL语句
            :param params: 参数
            :return: 结果
        """
        pass
