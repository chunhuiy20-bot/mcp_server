#  这是所有ORM模型的基类，提供公共字段和功能
from sqlalchemy import Column, Integer, DateTime, func, String, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from utils.SnowFlake import SnowflakeIDGenerator

# 创建SQLAlchemy基类
Base = declarative_base()

# 初始化雪花ID生成器（工作节点ID=1，数据中心ID=1）
generator = SnowflakeIDGenerator(worker_id=1, datacenter_id=1)


def generate_snowflake_id():
    """生成雪花算法ID"""
    return generator.generate()



class BaseEntity(Base):
    """所有模型的基类，包含公共字段"""
    __abstract__ = True  # 抽象类，不会创建表

    # default是在数据库层面执行的, id 本应该也是，但是__init__的时候，我们做了处理，给他赋予了值
    id = Column(BigInteger, primary_key=True, default=generate_snowflake_id)
    remark = Column(String(255), comment="备注", nullable=True)
    del_flag = Column(Integer, default=0, comment="逻辑删除标记")  # 0:未删除 1:已删除
    create_time = Column(DateTime, default=func.now(), comment="创建时间")
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    create_by = Column(String(50), nullable=True, default="1", comment="创建人,1表示系统默认")
    version = Column(Integer, default=0, comment="乐观锁")

    # 希望可以提前看到id
    def __init__(self, **kwargs):
        # 如果 id不在构造参数里面，提前调用generate_snowflake_id方法，为其赋值
        if "id" not in kwargs:
            kwargs["id"] = generate_snowflake_id()
        super().__init__(**kwargs)
