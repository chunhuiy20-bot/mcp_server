from typing import List, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar('T')


class PageResponse(BaseModel, Generic[T]):
    """分页响应数据"""
    list: List[T] = Field(description="数据列表")
    total: int = Field(description="总记录数")
    page_no: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")
    total_pages: int = Field(description="总页数")

    @classmethod
    def create(cls, data_list: List[T], total: int, page_no: int, page_size: int) -> 'PageResponse[T]':
        """创建分页响应"""
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        return cls(
            list=data_list,
            total=total,
            page_no=page_no,
            page_size=page_size,
            total_pages=total_pages
        )
