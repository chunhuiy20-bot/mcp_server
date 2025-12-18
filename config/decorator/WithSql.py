from typing import Optional, Callable
from functools import wraps

# ============= 装饰器定义 =============
def with_sql(sql: str, params: Optional[dict] = None):
    """第1步：装饰器工厂函数 - 接收SQL和params参数"""
    def decorator(func: Callable):
        """第2步：真正的装饰器 - 接收被装饰的函数"""
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            """第3步：包装函数 - 实际被调用的函数"""

            # 参数优先级处理
            final_sql = kwargs.pop('sql', None) or sql
            final_params = kwargs.pop('params', None) or params or {}

            # 调用原函数，注入sql和params
            return await func(self, sql=final_sql, params=final_params, *args, **kwargs)

        return wrapper

    return decorator