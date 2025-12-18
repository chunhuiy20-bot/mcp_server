from functools import wraps
from typing import Callable
from schemas.common.Result import Result

"""
    统一异常处理装饰器：
    将非Result的数据封装为Result，如果是Result直接返回Result
    如果报错，将错误信息封装到Result的message
"""



# 全局异常处理装饰器
def ExceptionHandlerAsyncDecorate(func: Callable) -> Callable:
    """统一异常处理装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            result = await func(*args, **kwargs)
            # 如果返回的不是 Result 对象，包装成 Result
            if not isinstance(result, Result):
                return Result(code=200, message="success", data=result)
            return result
        except Exception as e:
            return Result(code=500, message=str(e))
    return wrapper

# 同步函数版本的装饰器
def ExceptionHandlerSyncDecorate(func: Callable) -> Callable:
    """同步函数的统一异常处理装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            if not isinstance(result, Result):
                return Result(code=200, message="success", data=result)
            return result
        except Exception as e:
            return Result(code=500, message=str(e))
    return wrapper