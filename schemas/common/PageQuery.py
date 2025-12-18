from typing import Optional
from pydantic import BaseModel, Field, model_validator

"""
封装分页查询请求类
"""


class MySQLPageQuery(BaseModel):
    """MySQL分页请求参数 - 使用 model_validator"""

    DEFAULT_PAGE_SIZE: int = 20
    DEFAULT_PAGE_NUM: int = 1

    page_no: int = Field(default=DEFAULT_PAGE_NUM, ge=1, description="页码")
    page_size: int = Field(default=DEFAULT_PAGE_SIZE, ge=1, description="每页大小")
    sort_by: Optional[str] = Field(default=None, description="排序字段")
    is_asc: bool = Field(default=True, description="是否升序")

    @model_validator(mode='after')
    def validate_model(self) -> 'MySQLPageQuery':
        """模型级别验证"""
        if self.page_no < 1:
            raise ValueError('页码不能小于1')
        if self.page_size < 1:
            raise ValueError('每页大小不能小于1')
        if self.sort_by and not self.sort_by.replace('_', '').isalnum():
            raise ValueError('排序字段只能包含字母、数字和下划线')
        return self

    @property
    def offset(self) -> int:
        """
        计算偏移量
        @property 是一个装饰器，它的作用是将一个方法转换为属性，让我们可以像访问属性一样调用方法。
        适用 @property 的是属性，而不是行为（属性 vs 行为），以下情况：1、表示对象的状态或特征 2、基于现有属性的简单计算 3、获取不会改变对象状态的信息
        """
        return (self.page_no - 1) * self.page_size

    def to_sql_clause(self, default_sort_by: str = "id", default_is_asc: bool = True) -> str:
        """生成SQL分页和排序子句"""
        sort_field = self.sort_by or default_sort_by
        direction = "ASC" if (self.is_asc if self.sort_by else default_is_asc) else "DESC"

        return f"ORDER BY {sort_field} {direction} LIMIT {self.offset}, {self.page_size}"

