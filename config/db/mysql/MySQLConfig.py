import os
import time
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Callable, Any, Dict, Optional
from sqlalchemy import create_engine, QueuePool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool
from dotenv import load_dotenv
import asyncio
from sqlalchemy import text

load_dotenv()


class MultiAsyncDBManager:
    def __init__(self):
        self.databases: Dict[str, AsyncDBManager] = {}
        self.default_db: Optional[str] = None

    def add_database(self, name: str, database_url: str, **kwargs) -> 'AsyncDBManager':
        """添加数据库连接"""
        db_manager = AsyncDBManager(database_url=database_url, **kwargs)
        self.databases[name] = db_manager

        # 第一个添加的数据库作为默认数据库
        if self.default_db is None:
            self.default_db = name

        return db_manager

    def get_db(self, name: Optional[str] = None) -> 'AsyncDBManager':
        """获取指定数据库管理器"""
        db_name = name or self.default_db
        if db_name not in self.databases:
            raise ValueError(f"数据库 '{db_name}' 未配置")
        return self.databases[db_name]

    @asynccontextmanager
    async def session(self, db_name: Optional[str] = None) -> AsyncGenerator[AsyncSession, None]:
        """获取指定数据库的会话"""
        db_manager = self.get_db(db_name)
        async with db_manager.session() as session:
            yield session

    async def cleanup_all(self):
        """清理所有数据库连接"""
        for db_manager in self.databases.values():
            await db_manager.cleanup()


class AsyncDBManager:
    def __init__(self, database_url: Optional[str] = None, **config):
        # 如果没有传入 database_url，从环境变量读取
        self.DATABASE_URL = database_url or os.getenv("MYSQL_CONFIG_ASYNC")

        # 配置参数，支持传入覆盖
        self.POOL_SIZE = config.get("pool_size", int(os.getenv("DB_POOL_SIZE", "20")))
        self.MAX_OVERFLOW = config.get("max_overflow", int(os.getenv("DB_MAX_OVERFLOW", "10")))
        self.POOL_TIMEOUT = config.get("pool_timeout", int(os.getenv("DB_POOL_TIMEOUT", "30")))
        self.POOL_RECYCLE = config.get("pool_recycle", int(os.getenv("DB_POOL_RECYCLE", "1800")))

        # 创建异步引擎
        self.engine = create_async_engine(
            self.DATABASE_URL,
            poolclass=AsyncAdaptedQueuePool,
            pool_size=self.POOL_SIZE,
            max_overflow=self.MAX_OVERFLOW,
            pool_timeout=self.POOL_TIMEOUT,
            pool_recycle=self.POOL_RECYCLE,
            pool_pre_ping=True,
            echo=config.get("echo", True),
        )

        # 会话工厂
        self.SessionLocal = sessionmaker(
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
            bind=self.engine,
            expire_on_commit=False
        )

        # 统计信息
        self.start_time = time.time()
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(self.POOL_SIZE)

    # ... 其他方法保持不变 ...
    async def get_pool_status(self) -> dict:
        """获取连接池状态"""
        return {
            "pool_size": self.engine.pool.size(),
            "checked_in": self.engine.pool.checkedin(),
            "overflow": self.engine.pool.overflow(),
            "checked_out": self.engine.pool.checkedout(),
        }

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """上下文方式获取会话"""
        async with self.SessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def cleanup(self):
        """释放引擎资源"""
        await self.engine.dispose()

    async def check_health(self) -> bool:
        """健康检查"""
        try:
            async with self.session() as db:
                await db.execute(text("SELECT 1"))
            return True
        except Exception as e:
            print(f"[DB] 健康检查失败: {e}")
            return False


# 创建多数据库管理器
multi_db = MultiAsyncDBManager()

# 添加不同的数据库
multi_db.add_database("main", os.getenv("MYSQL_CONFIG_ASYNC"))
multi_db.add_database("db2", os.getenv("MYSQL_CONFIG_ASYNC2"))



#
# # 使用示例
# async def main():
#     # 创建多数据库管理器
#     multi_db = MultiAsyncDBManager()
#
#     # 添加不同的数据库
#     multi_db.add_database("main", os.getenv("MYSQL_CONFIG_ASYNC"))
#     multi_db.add_database("db2", os.getenv("MYSQL_CONFIG_ASYNC2"))
#
#     try:
#         # 使用主数据库
#         async with multi_db.session("main") as session:
#             result = await session.execute(text("SELECT * FROM plate_device LIMIT 5"))
#             rows = result.fetchall()
#             print("主数据库结果:", rows)
#
#         # 使用分析数据库
#         async with multi_db.session("db2") as session:
#             result = await session.execute(text("SELECT COUNT(*) FROM prompts"))
#             count = result.scalar()
#             print("分析数据库事件数:", count)
#
#     finally:
#         await multi_db.cleanup_all()
#
#
# if __name__ == '__main__':
#     asyncio.run(main())
