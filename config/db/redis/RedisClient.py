import json
import asyncio
from typing import Optional, Union, Any, Dict
from redis.asyncio import Redis as AsyncRedis
from redis.asyncio.connection import ConnectionPool as AsyncConnectionPool


class AsyncRedisClient:
    """
    Redis 操作工具类（支持同步/异步）
    """

    def __init__(
        self,
        host: str = "8.130.81.134",
        port: int = 6379,
        password: Optional[str] = "137139yang@",
        db: int = 0,
        max_connections: int = 10,
        decode_responses: bool = True
    ):
        # 初始化 Redis 连接参数
        self._host = host
        self._port = port
        self._password = password
        self._db = db
        self._max_connections = max_connections
        self._decode_responses = decode_responses

        # 连接池初始化
        self._async_pool: Optional[AsyncConnectionPool] = None



    async def async_client(self) -> AsyncRedis:
        """获取异步 Redis 客户端"""
        if self._async_pool is None:
            self._async_pool = AsyncConnectionPool(
                host=self._host,
                port=self._port,
                password=self._password,
                db=self._db,
                max_connections=self._max_connections,
                decode_responses=self._decode_responses
            )
        return AsyncRedis(connection_pool=self._async_pool)



    async def async_set(self, key: str, value: Union[str, dict, list], ex: Optional[int] = None) -> bool:
        """异步设置键值对"""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        client = await self.async_client()
        return await client.set(key, value, ex=ex)

    async def async_get(self, key: str, default: Any = None) -> Any:
        """异步获取键值"""
        client = await self.async_client()
        value = await client.get(key)
        if value is None:
            return default
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    async def async_delete(self, *keys: str) -> int:
        """异步删除键"""
        client = await self.async_client()
        return await client.delete(*keys)

    # ---------------- Hash 操作 ----------------
    async def async_hset(self, name: str, key: str, value: Any):
        """异步设置哈希字段"""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        client = await self.async_client()
        return await client.hset(name, key, value)

    async def async_hget(self, name: str, key: str, as_json: bool = False):
        """异步获取哈希字段"""
        client = await self.async_client()
        value = await client.hget(name, key)
        if as_json and value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return value

    async def async_hgetall(self, name: str):
        """异步获取所有哈希字段"""
        client = await self.async_client()
        return await client.hgetall(name)

    # ---------------- List 操作 ----------------
    async def async_lpush(self, name: str, *values: Any):
        """异步从左侧插入列表元素"""
        client = await self.async_client()
        return await client.lpush(name, *values)

    async def async_rpush(self, name: str, *values: Any):
        """异步从右侧插入列表元素"""
        client = await self.async_client()
        return await client.rpush(name, *values)

    async def async_lpop(self, name: str):
        """异步从左侧弹出列表元素"""
        client = await self.async_client()
        return await client.lpop(name)

    async def async_rpop(self, name: str):
        """异步从右侧弹出列表元素"""
        client = await self.async_client()
        return await client.rpop(name)

    async def async_lrange(self, name: str, start: int, end: int):
        """异步获取列表范围内的元素"""
        client = await self.async_client()
        return await client.lrange(name, start, end)

    # ---------------- Set 操作 ----------------
    async def async_sadd(self, name: str, *values: Any):
        """异步向集合添加元素"""
        client = await self.async_client()
        return await client.sadd(name, *values)

    async def async_smembers(self, name: str):
        """异步获取集合所有成员"""
        client = await self.async_client()
        return await client.smembers(name)

    async def async_srem(self, name: str, *values: Any):
        """异步从集合中移除元素"""
        client = await self.async_client()
        return await client.srem(name, *values)

    # ---------------- Sorted Set 操作 ----------------
    async def async_zadd(self, name: str, mapping: Dict[str, float]):
        """异步向有序集合添加成员"""
        client = await self.async_client()
        return await client.zadd(name, mapping)

    async def async_zrange(self, name: str, start: int, end: int, desc: bool = False, withscores: bool = True):
        """异步获取有序集合范围内的成员"""
        client = await self.async_client()
        return await client.zrange(name, start, end, desc=desc, withscores=withscores)

    async def async_zrem(self, name: str, *values: Any):
        """异步从有序集合中移除成员"""
        client = await self.async_client()
        return await client.zrem(name, *values)

    # ---------------- 其他实用方法 ----------------
    async def async_exists(self, key: str) -> bool:
        """异步检查键是否存在"""
        client = await self.async_client()
        return bool(await client.exists(key))

    async def async_expire(self, key: str, seconds: int):
        """异步为键设置过期时间"""
        client = await self.async_client()
        return await client.expire(key, seconds)

    async def async_incr(self, key: str, amount: int = 1):
        """异步增加键的整数值"""
        client = await self.async_client()
        return await client.incr(key, amount)

    async def async_decr(self, key: str, amount: int = 1):
        """异步减少键的整数值"""
        client = await self.async_client()
        return await client.decr(key, amount)

    # ---------------- 发布/订阅 ----------------
    async def publish(self, channel: str, message: Union[str, dict]):
        """异步发布消息到频道"""
        if isinstance(message, dict):
            message = json.dumps(message)
        client = await self.async_client()
        await client.publish(channel, message)

    async def subscribe(self, channel: str):
        """异步订阅频道"""
        client = await self.async_client()
        pubsub = client.pubsub()
        await pubsub.subscribe(channel)
        return pubsub


async def main():
    redis: AsyncRedisClient = AsyncRedisClient()


    # ---------------- KV ----------------
    print("\n--- KV ---")
    await redis.async_set("user:1", {"name": "小杨", "age": 28}, ex=10)
    user = await redis.async_get("user:1")
    print("读取 user:1 =>", user)
    #
    # await redis.async_incr("counter")
    # await redis.async_incr("counter", 5)
    # print("counter =>", await redis.async_get("counter"))
    #
    # await redis.async_expire("user:1", 30)
    # print("user:1 是否存在 =>", await redis.async_exists("user:1"))
    #
    # # ---------------- Hash ----------------
    # print("\n--- Hash ---")
    # await redis.async_hset("hash:user", "name", "小杨")
    # await redis.async_hset("hash:user", "age", 28)
    # print("hget name =>", await redis.async_hget("hash:user", "name"))
    # print("hgetall =>", await redis.async_hgetall("hash:user"))
    #
    # # ---------------- List ----------------
    # print("\n--- List ---")
    # await redis.async_lpush("list:tasks", "task1", "task2")
    # await redis.async_rpush("list:tasks", "task3")
    # print("lrange =>", await redis.async_lrange("list:tasks", 0, -1))
    # print("lpop =>", await redis.async_lpop("list:tasks"))
    # print("rpop =>", await redis.async_rpop("list:tasks"))
    #
    # # ---------------- Set ----------------
    # print("\n--- Set ---")
    # await redis.async_sadd("set:tags", "python", "redis", "asyncio")
    # print("smembers =>", await redis.async_smembers("set:tags"))
    # await redis.async_srem("set:tags", "redis")
    # print("删除 redis 后 =>", await redis.async_smembers("set:tags"))
    #
    # # ---------------- Sorted Set ----------------
    # print("\n--- Sorted Set ---")
    # await redis.async_zadd("zset:scores", {"Tom": 90, "Jerry": 85, "Spike": 92})
    # print("zrange with score =>", await redis.async_zrange("zset:scores", 0, -1))
    # await redis.async_zrem("zset:scores", "Jerry")
    # print("删除 Jerry 后 =>", await redis.async_zrange("zset:scores", 0, -1))
    #
    # # ---------------- 发布/订阅 ----------------
    # print("\n--- 发布/订阅 ---")
    #
    # async def subscriber():
    #     sub_client = await redis.async_client()
    #     pubsub = sub_client.pubsub()
    #     await pubsub.subscribe("news")
    #     print("📡 订阅 news 频道中... 等待消息...")
    #     async for message in pubsub.listen():
    #         if message["type"] == "message":
    #             print("收到消息：", message["data"])
    #             break  # 收到一条消息就退出
    #
    # async def publisher():
    #     await asyncio.sleep(1)  # 等待订阅生效
    #     await redis.publish("news", {"title": "Redis 异步测试", "content": "Hello 小杨!"})

    # await asyncio.gather(subscriber(), publisher())


if __name__ == "__main__":
    asyncio.run(main())
