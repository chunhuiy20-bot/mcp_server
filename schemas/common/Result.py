from typing import Generic, Optional, TypeVar
from pydantic import BaseModel, Field, ConfigDict
"""
    统一返回类，这个完全与java服务一致，方便前端使用
"""
# 定义一个泛型类型 T
T = TypeVar('T')


class Result(BaseModel, Generic[T]):
    code: int = Field(default=200, description="状态码，默认为 200")
    message: str = Field(default="success", description="返回消息，默认为 success")
    data: Optional[T] = Field(default=None, description="返回的数据，默认为 None")

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
