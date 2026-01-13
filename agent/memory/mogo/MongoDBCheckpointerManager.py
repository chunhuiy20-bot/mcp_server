"""
这个是基于langgraph的Mongodb做内存检查点，作为长期记忆
核心功能: 1、使用Mongodb作为检查点，存储用户与ai的聊天记录
        2、初始化的时候，用户传参优先，否则使用env作为核心配置
"""
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from langgraph.checkpoint.mongodb import MongoDBSaver
import os
from dotenv import load_dotenv

load_dotenv()


class MongoDBCheckpointerManager:
    """MongoDB 检查点管理器"""

    def __init__(
        self,
        mongodb_uri: str = None,
        db_name: str = None,
        checkpoint_collection: str = None,
        writes_collection: str = None
    ):
        self._checkpointer = None
        self._client = None

        # 用户传参 > 环境变量
        self._MONGODB_URI = mongodb_uri or os.getenv("MONGODB_URI")
        self._MONGODB_DB_NAME = db_name or os.getenv("MONGODB_DB")
        self._MONGODB_CHECKPOINT_COLLECTION_NAME = checkpoint_collection or os.getenv("MONGODB_CHECKPOINT_COLLECTION_NAME")
        self._MONGODB_WRITES_COLLECTION_NAME = writes_collection or os.getenv("MONGODB_WRITES_COLLECTION_NAME")

        self._init_mongodb()

    def _init_mongodb(self):
        """初始化 MongoDB 连接和检查点存储器"""
        try:
            self._client = MongoClient(self._MONGODB_URI, serverSelectionTimeoutMS=5000)
            self._client.admin.command('ping')
            print(f"MongoDB 连接成功: {self._MONGODB_URI}")
            self._checkpointer = MongoDBSaver(
                client=self._client,
                db_name=self._MONGODB_DB_NAME,
                checkpoint_collection_name=self._MONGODB_CHECKPOINT_COLLECTION_NAME,
                writes_collection_name=self._MONGODB_WRITES_COLLECTION_NAME
            )
            print(f"MongoDB 检查点存储器初始化成功: {self._MONGODB_DB_NAME}")
        except Exception as e:
            print(f"MongoDB 初始化失败: {e}")

    def get_checkpointer(self):
        """获取检查点存储器"""
        return self._checkpointer

    def cleanup(self):
        """清理资源"""
        if self._client:
            self._client.close()
            print("MongoDB 连接已关闭")
