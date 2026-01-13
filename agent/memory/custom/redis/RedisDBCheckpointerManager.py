import asyncio
import os
from typing import Optional
from dotenv import load_dotenv
from agent.memory.custom.redis.RedisClient import AsyncRedisClient
from agent.memory.custom.redis.my_checkpoints.CustomRedisCheckpointAdapter import CustomRedisCheckpointAdapter  # 替换为实际的导入路径
load_dotenv()

"""
    这个是基于Redis做langgraph内存检查点，作为长期记忆
"""


class RedisDBCheckpointerManager:
    """Redis 检查点管理器"""

    def __init__(self, max_length: Optional[int] = 100):
        self._checkpointer = None
        self._redis_client = None
        self._REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
        self._REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
        self._REDIS_DB = int(os.getenv("REDIS_DB", 0))
        self._REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
        self._REDIS_URI = os.getenv("REDIS_URI", None)  # 可选的完整 URI
        self.max_length = max_length
        self._init_redis()


    def _init_redis(self):
        """初始化 Redis 连接和检查点存储器"""
        try:

            # 创建 Redis 客户端
            if self._REDIS_URI:
                # 如果提供了完整的 URI，使用 URI 连接
                self._redis_client = AsyncRedisClient()
            else:
                print(f"使用 Redis 参数连接: {self._REDIS_HOST}:{self._REDIS_PORT}")
                # 否则使用单独的参数连接
                self._redis_client = AsyncRedisClient()

            # 创建检查点适配器
            self._checkpointer = CustomRedisCheckpointAdapter(
                redis_client=self._redis_client,
                max_length=self.max_length
            )

            print(f"Redis 检查点适配器初始化成功")

        except Exception as e:
            print(f"Redis 连接失败: {e}")
            raise RuntimeError("Redis 初始化失败，程序启动终止") from e

    async def _test_connection(self):
        """测试 Redis 连接"""
        try:
            if hasattr(self._redis_client, 'async_ping'):
                await self._redis_client.async_ping()
            elif hasattr(self._redis_client, 'ping'):
                await self._redis_client.ping()
            else:
                await self._redis_client.async_get("__test_connection__")
        except Exception as e:
            raise ConnectionError(f"Redis 连接测试失败: {e}") from e

    def get_checkpointer(self):
        """获取检查点存储器"""
        return self._checkpointer

    async def cleanup(self):
        """清理资源"""
        if self._redis_client:
            await self._redis_client.close()
            print("Redis 连接已关闭")


async def example_usage():
    """测试 Redis 检查点管理器（异步版本）"""
    try:
        # 创建 Redis 检查点管理器
        redis_checkpointer_manager = RedisDBCheckpointerManager()

        # 获取检查点存储器
        checkpointer = redis_checkpointer_manager.get_checkpointer()

        print("检查点存储器已获取")
        print(f"检查点类型: {type(checkpointer)}")
        print(f"检查点对象: {checkpointer}")

        # 测试检查点功能（可选）
        # 这里可以添加更多的测试逻辑

        # 清理资源
        redis_checkpointer_manager.cleanup()

        print("测试完成")

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(example_usage())
