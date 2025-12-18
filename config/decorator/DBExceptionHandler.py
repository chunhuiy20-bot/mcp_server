from functools import wraps
import traceback

def DBExceptionHandler(func):
    """
    异步装饰器：捕获异常并在 finally 中统一清理数据库资源
    """
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except Exception as e:
            print(f"{func.__name__} 执行失败: {e}")
            traceback.print_exc()
            raise
        finally:
            if hasattr(self, "db_manager") and hasattr(self.db_manager, "cleanup"):
                await self.db_manager.cleanup()
    return wrapper
