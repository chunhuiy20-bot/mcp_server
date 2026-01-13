import os
import json
from typing import Optional, Union, Any, Dict
from langchain_core.load import dumps, loads
from langchain_core.messages import HumanMessage, BaseMessage, AIMessage, ToolMessage
from redis.asyncio import Redis as AsyncRedis
from redis.asyncio.connection import ConnectionPool as AsyncConnectionPool
from dotenv import load_dotenv
import warnings
warnings.filterwarnings("ignore", message=".*The function `loads` is in beta.*")  # from langchain_core.load import loads 的时候, langchain_core的loads模块还在开发中，后续可能会变更，目前先忽略这个警告


class AsyncRedisClient:
    """
    Redis 操作工具类（支持同步/异步）
    """

    def __init__(
        self,
        max_connections: int = 10,
        decode_responses: bool = True
    ):
        # 初始化 Redis 连接参数
        self._host = os.getenv("REDIS_HOST")
        self._port = os.getenv("REDIS_PORT")
        self._password = os.getenv("REDIS_PASSWORD", None)
        self._db = os.getenv("REDIS_DB")
        self._max_connections = max_connections
        self._decode_responses = decode_responses

        # 连接池初始化
        self._async_pool: Optional[AsyncConnectionPool] = None

    async def async_client(self) -> AsyncRedis:
        """获取异步 Redis 客户端"""
        if self._async_pool is None:
            if self._password == "" or self._password is None:
                self._password = ""
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
        return await client.publish(channel, message)

    async def subscribe(self, channel: str):
        """异步订阅频道并返回 pubsub 对象"""
        client = await self.async_client()
        pubsub = client.pubsub()
        await pubsub.subscribe(channel)
        return pubsub

    async def unsubscribe(self, pubsub, *channels):
        """取消订阅"""
        await pubsub.unsubscribe(*channels)

    async def close_pubsub(self, pubsub):
        """关闭 pubsub 连接"""
        await pubsub.close()

    # --------------- bitmap 操作 ---------------
    async def async_setbit(self, key: str, offset: int, value: int) -> int:
        """
        异步设置 bitmap 中指定偏移位的值
        :param key: bitmap 键名
        :param offset: 偏移量
        :param value: 值 (0 或 1)
        :return: 该偏移位原来的值
        """
        client = await self.async_client()
        return await client.setbit(key, offset, value)

    async def async_getbit(self, key: str, offset: int) -> int:
        """
        异步获取 bitmap 中指定偏移位的值
        :param key: bitmap 键名
        :param offset: 偏移量
        :return: 该偏移位的值 (0 或 1)
        """
        client = await self.async_client()
        return await client.getbit(key, offset)

    async def async_bitcount(self, key: str, start: int = 0, end: int = -1) -> int:
        """
        异步统计 bitmap 中值为 1 的位的数量
        :param key: bitmap 键名
        :param start: 起始字节位置
        :param end: 结束字节位置
        :return: 值为 1 的位的数量
        """
        client = await self.async_client()
        return await client.bitcount(key, start, end)


    async def async_bitop(self, operation: str, dest_key: str, *keys: str) -> int:
        """
        异步对多个 bitmap 进行位运算
        :param operation: 位运算类型 (AND, OR, XOR, NOT)
        :param dest_key: 结果存储的目标键
        :param keys: 参与运算的源键
        :return: 结果 bitmap 的长度（字节数）
        """
        client = await self.async_client()
        return await client.bitop(operation, dest_key, *keys)

    async def async_bitfield(self, key: str, *operations: Any) -> list:
        """
        异步对 bitmap 进行复杂的位域操作
        :param key: bitmap 键名
        :param operations: 位域操作指令
        :return: 操作结果列表
        """
        client = await self.async_client()
        return await client.bitfield(key, *operations)

    # ---------------- 消息队列操作（默认最多100条） ----------------
    async def async_add_message_to_queue(
            self,
            user_id: str,
            message: BaseMessage,
            max_length: int = 100
    ) -> tuple[bool, list[BaseMessage]]:
        """
        异步添加消息到用户消息队列（默认最多保留100条，FIFO）
        如果移除的消息是 HumanMessage，会继续移除直到下一个 HumanMessage（保证完整对话）
        :param user_id: 用户ID
        :param message: LangChain 消息对象
        :param max_length: 最大消息条数
        :return: (是否成功, 被移除的消息列表)
        """

        key = f"user:message:queue:{user_id}"
        serialized = dumps(message)
        client = await self.async_client()
        removed_messages = []  # 收集被移除的消息

        # 从右侧（末尾）添加消息
        await client.rpush(key, serialized)

        # 检查列表长度
        current_length = await client.llen(key)

        if current_length <= max_length:
            return True, removed_messages

        # 需要移除消息
        remove_count = current_length - max_length

        # 读取可能被移除的消息范围
        search_limit = min(current_length, remove_count + 50)
        messages_data = await client.lrange(key, 0, search_limit - 1)

        if not messages_data:
            # 没有消息，直接删除最后几条
            removed_data = await client.lrange(key, 0, remove_count - 1)
            for data in removed_data:
                try:
                    removed_messages.append(loads(data))
                except Exception as e:
                    print(f"反序列化被移除的消息失败: {e}")
            await client.ltrim(key, -max_length, -1)
            return True, removed_messages

        # 检查第一条要移除的消息
        try:
            first_message = loads(messages_data[0])
        except Exception as e:
            print(f"反序列化第一条消息失败: {e}")
            # 反序列化失败，正常删除
            removed_data = await client.lrange(key, 0, remove_count - 1)
            for data in removed_data:
                try:
                    removed_messages.append(loads(data))
                except Exception as e:
                    print(f"反序列化被移除的消息失败: {e}")
            await client.ltrim(key, -max_length, -1)
            return True, removed_messages

        # 如果第一条是 HumanMessage，查找下一个 HumanMessage
        if isinstance(first_message, HumanMessage):
            next_human_index = -1
            for i in range(1, len(messages_data)):
                try:
                    msg = loads(messages_data[i])
                    if isinstance(msg, HumanMessage):
                        next_human_index = i
                        break
                except Exception as e:
                    continue

            if next_human_index != -1:
                # 找到下一个 HumanMessage，收集要移除的消息
                removed_data = await client.lrange(key, 0, next_human_index - 1)
                for data in removed_data:
                    try:
                        removed_messages.append(loads(data))
                    except Exception as e:
                        print(f"反序列化被移除的消息失败: {e}")
                # 保留从下一个 HumanMessage 开始的所有消息
                await client.ltrim(key, next_human_index, -1)
            else:
                # 没找到下一个 HumanMessage，收集要移除的消息
                removed_data = await client.lrange(key, 0, remove_count - 1)
                for data in removed_data:
                    try:
                        removed_messages.append(loads(data))
                    except Exception as e:
                        print(f"反序列化被移除的消息失败: {e}")
                await client.ltrim(key, -max_length, -1)
        else:
            # 第一条不是 HumanMessage，正常删除并收集
            removed_data = await client.lrange(key, 0, remove_count - 1)
            for data in removed_data:
                try:
                    removed_messages.append(loads(data))
                except Exception as e:
                    print(f"反序列化被移除的消息失败: {e}")
            await client.ltrim(key, -max_length, -1)

        return True, removed_messages

    async def async_get_message_queue(self, user_id: str) -> list[BaseMessage]:
        """
        异步获取用户消息队列（按时间顺序）
        :param user_id: 用户ID
        :return: 消息对象列表（按顺序）
        """
        key = f"user:message:queue:{user_id}"
        client = await self.async_client()

        # 获取所有消息（从左到右，即从早到晚）
        values = await client.lrange(key, 0, -1)

        messages = []
        for value in values:
            try:
                message = loads(value)
                messages.append(message)
            except Exception as e:
                print(f"反序列化失败: {e}")
                continue

        return messages

    async def async_clear_message_queue(self, user_id: str) -> int:
        """
        清空用户消息队列
        :param user_id: 用户ID
        :return: 删除的消息数量
        """
        key = f"user:message:queue:{user_id}"
        return await self.async_delete(key)


    async def close(self):
        """关闭连接池"""
        if self._async_pool:
            await self._async_pool.disconnect()
            self._async_pool = None









import asyncio
async def main():
    redis:AsyncRedisClient = AsyncRedisClient()
    from langchain_core.load import dumps, loads
    # ---------------- KV ----------------
    # print("\n--- KV ---")
    # await redis.async_set("user:1", {"name": "小杨", "age": 28}, ex=10)
    # user = await redis.async_get("user:1")
    # print("读取 user:1 =>", user["name"], type(user["age"]))

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
    # ---------------- 发布/订阅 ----------------
    # print("\n--- 发布/订阅 ---")
    # await redis.async_set("user:1", {"name": "小杨", "age": 28}, ex=10)
    # user = await redis.async_get("user:1")
    # print("读取 user:1 =>", user)
    #
    # async def subscriber():
    #     pubsub = await redis.subscribe("news")
    #     print("📡 订阅 news 频道中... 等待消息...")
    #
    #     try:
    #         async for message in pubsub.listen():
    #             if message["type"] == "subscribe":
    #                 print(f"✅ 成功订阅频道: {message['channel']}")
    #                 continue
    #
    #             if message["type"] == "message":
    #                 data = message["data"]
    #                 try:
    #                     # 尝试解析 JSON
    #                     data = json.loads(data)
    #                 except:
    #                     pass
    #                 print(f"收到消息: {data}")
    #
    #                 # 收到消息后取消订阅并退出
    #                 await redis.unsubscribe(pubsub, "news")
    #                 break
    #     except Exception as e:
    #         print(f"订阅出错: {e}")
    #     finally:
    #         await redis.close_pubsub(pubsub)
    #         print("🔚 订阅连接已关闭")
    #
    # async def publisher():
    #     await asyncio.sleep(1)  # 等待订阅生效
    #     print("📤 发布消息...")
    #     result = await redis.publish("news", {"title": "Redis 异步测试", "content": "Hello 小杨!"})
    #     print(f"消息发布结果: {result} 个客户端收到")
    #
    # # 运行测试
    # await asyncio.gather(subscriber(), publisher(), return_exceptions=True)

    # import hashlib
    #
    # contact = "2609060093"
    # md5_hash = hashlib.md5(contact.encode('utf-8')).digest()
    # offset = int.from_bytes(md5_hash[:4], byteorder='big')
    # print("偏移量：",offset)
    # contact2 = "2609060093@qq.com"
    # md5_hash2 = hashlib.md5(contact2.encode('utf-8')).digest()
    # offset2 = int.from_bytes(md5_hash2[:4], byteorder='big')
    # print(await redis.async_setbit("phone:contact", offset, 1))
    # print(await redis.async_setbit("phone:contact", offset2, 1))
    # print(await redis.async_getbit("phone:contact", 1205))
    # print(await redis.async_bitcount("phone:contact"))

    # s = "aaa1231231321av"
    # print(s[-1])


async def quick_test():
    """快速测试消息队列"""
    redis: AsyncRedisClient = AsyncRedisClient()

    user_id = "1008611"

    # print("=" * 50)
    # print(f"测试用户 {user_id} 的消息队列")
    # print("=" * 50)
    #
    # # 模拟对话：用户和AI交替发送消息
    # conversations = [
    #     ("user", "你叫什么名字"),
    #     ("ai", "我是一个AI助手，很高兴为您服务！"),
    #     ("user", "你能做什么？"),
    #     ("ai", "我可以回答问题、提供帮助、进行对话等。"),
    #     ("user", "今天天气怎么样？"),
    #     ("ai", "抱歉，我无法获取实时天气信息。"),
    #     ("user", "谢谢你的回答"),  # 第7条，会移除最早的
    #     ("ai", "不客气，很高兴能帮助您！"),  # 第8条，会移除第2条
    # ]
    #
    # # 添加消息
    # for i, (role, content) in enumerate(conversations, 1):
    #     if role == "user":
    #         message = HumanMessage(content)
    #     else:
    #         message = AIMessage(content)
    #
    #     await redis.async_add_message_to_queue(user_id, message)
    #     print(f"\n[{i}] 添加{'用户' if role == 'user' else 'AI'}消息: {content}")


    # 最终查看所有消息
    # print("\n" + "=" * 50)
    # print("最终消息队列（按顺序）:")
    # print("=" * 50)
    # final_messages = await redis.async_get_message_queue(user_id)
    #
    # # enumerate 是 Python 的内置函数，用于在遍历列表、元组等可迭代对象时同时获取索引和值。
    # for i, msg in enumerate(final_messages, 1):
    #     msg_type = "用户" if isinstance(msg, HumanMessage) else "AI"
    #     print(f"[{i}] {msg_type}消息: {msg.content}")
    #     print(type(msg))



    # 清理（可选）
    await redis.async_clear_message_queue(user_id)
    print("队列已清空")


async def quick_demo():
    """快速演示"""
    redis = AsyncRedisClient()
    user_id = "1008611"

    # 清空队列
    # await redis.async_clear_message_queue(user_id)

    # 添加一些消息
    print("添加消息...")
    messages = [
        HumanMessage(content="你好"),
        AIMessage(content="您好！"),
        HumanMessage(content="查询余额"),
        AIMessage(content="", tool_calls=[{
            'id': 'call_001',
            'name': '查询余额',
            'args': {}
        }]),
        ToolMessage(content="余额100元", tool_call_id='call_001'),
        AIMessage(content="您的余额是100元"),
    ]

    for msg in messages:
        success, removed = await redis.async_add_message_to_queue(
            user_id,
            msg,
            max_length=100
        )
        if removed:
            print(removed)
            print(f"移除了 {len(removed)} 条消息")

    # 查看最终队列
    print("\n最终队列:")
    final = await redis.async_get_message_queue(user_id)
    for i, msg in enumerate(final, 1):
        print(f"  {i}. [{type(msg).__name__}] {msg.content[:50]}")



# 运行
if __name__ == "__main__":
    # asyncio.run(main())
    # asyncio.run(quick_test())
    asyncio.run(quick_demo())