import asyncio
import time

from openai import OpenAI
from typing import List, Optional
import os
from dotenv import load_dotenv
from pymilvus import MilvusClient

from schemas.common.Result import Result

load_dotenv()


class OpenAIMemorySystem:
    """基于 OpenAI Embeddings 的记忆系统"""

    def __init__(
            self,
            api_key: Optional[str] = os.getenv("OPENAI_API_KEY"),
            base_url: Optional[str] = os.getenv("OPENAI_BASE_URL"),
            embedding_model: Optional[str] = "text-embedding-3-small",
            collection_name: Optional[str] = "long_memory",
    ):
        """
        初始化记忆系统
        Args:
            api_key: OpenAI API Key
            base_url: Openai url
            embedding_model: 嵌入模型
                - text-embedding-3-small: 便宜，快速 ($0.02/1M tokens)
                - text-embedding-3-large: 质量更高 ($0.13/1M tokens)
                - text-embedding-ada-002: 旧版本 ($0.10/1M tokens)
        """
        # 1. 初始化 OpenAI 客户端
        print(f"🔄 使用 OpenAI 模型: {embedding_model}, {base_url} ,{api_key}")
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.embedding_model = embedding_model
        self.collection_name = collection_name
        # 2.初始化向量数据库
        self.milvus_vector_db_client = MilvusClient(
            uri=os.getenv("VECTOR_DB_URL"),
            token=os.getenv("VECTOR_DB_TOKEN")
        )


    async def get_embedding(self, text: str, dimensions: Optional[int] = 1536) -> List[float]:
        """
        获取文本的向量嵌入
        Args:
            text: 输入文本
            dimensions: 向量纬度
        Returns:
            向量列表
        """
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=text,
            dimensions=dimensions,
            encoding_format="float"
        )

        return response.data[0].embedding

    async def add_memory(self, user_id: str, content: str):
        """
        添加向量文本
        :param user_id:
        :param content:
        :return:
        """
        # 1. 文本转向量
        vector = await self.get_embedding(content)
        # 2. 构建存储结构
        memory_id = int(time.time() * 1000000) % 9223372036854775807
        data = {
            "primary_key": memory_id,
            "user_id": user_id,
            "content": content,
            "vector": vector
        }
        # 3. 存储向量
        result = self.milvus_vector_db_client.insert(
            collection_name=self.collection_name,
            data=[data]
        )

        # 4. 输出result
        print(f"✅ 向量存储成功: {result}")
        return Result(code=200, data=result)

    async def search_memories(self, user_id: str, query: str, limit: int = 5):
        """
           搜索相关记忆
           Args:
               user_id: 用户ID
               query: 查询文本
               limit: 返回数量
           Returns:
               记忆列表
        """

        # 1，向量化
        query_vector = await self.get_embedding(query)


        # 2. 搜索
        results = self.milvus_vector_db_client.search(
            collection_name=self.collection_name,
            data=[query_vector],
            filter=f'user_id == "{user_id}"',  # 只搜索该用户的记忆
            limit=limit,
            output_fields=["user_id", "content"]  # 返回这些字段
        )
        print(f"未经过过滤的搜索结果: {results}")
        # 3. 过滤相似度 >= 0.8 的结果
        # 3. 按置信度分级
        high_confidence = []  # 高置信度 >= 0.9
        medium_confidence = []  # 中置信度 0.7 - 0.9
        low_confidence = []  # 低置信度 0.5 - 0.7
        low_related = []  # 低相关度 <= 0.5
        for hits in results:
            for hit in hits:
                similarity = hit['distance']

                memory = {
                    "id": hit['primary_key'],
                    "content": hit['entity']['content'],
                    "similarity": round(similarity, 4),
                    "user_id": hit['entity']['user_id']
                }

                # 分级
                if similarity >= 0.9:
                    memory["confidence"] = "high"
                    high_confidence.append(memory)
                elif similarity >= 0.7:
                    memory["confidence"] = "medium"
                    medium_confidence.append(memory)
                elif similarity >= 0.5:
                    memory["confidence"] = "low"
                    low_confidence.append(memory)
                else:
                    memory["confidence"] = "low_related"
                    low_related.append(memory)

        result = {
            "high": high_confidence,
            "medium": medium_confidence,
            "low": low_confidence,
            "low_related": low_related,
            "total": len(high_confidence) + len(medium_confidence) + len(low_confidence)
        }
        print(f"🔍 找到记忆: 高={len(high_confidence)}, 中={len(medium_confidence)}, 低={len(low_confidence)}")
        return Result(data=result)

    async def delete_memory(self, memory_id: int):
        """
        根据 primary_key 删除记忆
        Args:
            memory_id: 记忆的 primary_key
        Returns:
            删除结果
        """
        try:
            # 删除
            self.milvus_vector_db_client.delete(
                collection_name=self.collection_name,
                filter=f"primary_key == {memory_id}"
            )

            print(f"🗑记忆已删除: {memory_id}")
            return Result(code=200, message=f"删除{memory_id}记忆成功", data=True)

        except Exception as e:
            print(f"删除失败: {str(e)}")
            return Result(code=500, message=f"删除失败: {str(e)}", data=False)


# 全局实例
memory_system = OpenAIMemorySystem()



async def test():
    # res = await memory_system.get_embedding("你好")
    # res = await memory_system.add_memory("1008611", "我是个java和python程序员")
    res = await memory_system.search_memories(user_id="1008611", query="用户学过什么程序语言，编程语言，诸如：java，python，c，c++,vs,html,js,ts等")
    print(res)
    print(await memory_system.delete_memory(1766730230596687))
    print(await memory_system.delete_memory(1766729624278273))


if __name__ == "__main__":
    asyncio.run(test())



