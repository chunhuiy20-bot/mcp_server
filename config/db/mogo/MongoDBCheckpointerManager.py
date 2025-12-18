from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from langgraph.checkpoint.mongodb import MongoDBSaver
import os
from dotenv import load_dotenv


load_dotenv()


"""
    这个是基于Mongodb做langgraph内存检查点，作为长期记忆
"""


class MongoDBCheckpointerManager:
    """MongoDB 检查点管理器"""

    def __init__(self):
        self._checkpointer = None
        self._client = None
        self._MONGODB_URI = os.getenv("MONGODB_URI")
        self._MONGODB_DB_NAME = os.getenv("MONGODB_DB")
        self._MONGODB_CHECKPOINT_COLLECTION_NAME = os.getenv("MONGODB_CHECKPOINT_COLLECTION_NAME")
        self._MONGODB_WRITES_COLLECTION_NAME = os.getenv("MONGODB_WRITES_COLLECTION_NAME")
        self._init_mongodb()

    def _init_mongodb(self):
        """初始化 MongoDB 连接和检查点存储器"""
        try:
            # 创建 MongoDB 客户端
            self._client = MongoClient(self._MONGODB_URI, serverSelectionTimeoutMS=5000)

            # 测试连接
            self._client.admin.command('ping')
            print(f"MongoDB 连接成功: {self._MONGODB_URI}")

            # 创建检查点存储器
            self._checkpointer = MongoDBSaver(
                client=self._client,
                db_name=self._MONGODB_DB_NAME
            )

            print(f"MongoDB 检查点存储器初始化成功: {self._MONGODB_DB_NAME}")

        except ConnectionFailure as e:
            print(f"MongoDB 连接失败: {e}")
            raise RuntimeError("MongoDB 初始化失败，程序启动终止") from e
        except Exception as e:
            print(f"MongoDB 初始化失败: {e}")
            raise RuntimeError("MongoDB 初始化失败，程序启动终止") from e

    def get_checkpointer(self):
        """获取检查点存储器"""
        return self._checkpointer

    def cleanup(self):
        """清理资源"""
        if self._client:
            self._client.close()
            print("MongoDB 连接已关闭")
