from typing import Optional, Type, TypeVar, Generic, List, Any
from sqlalchemy import text, inspect
from config.db.mysql.MySQLConfig import MultiAsyncDBManager, multi_db
from config.decorator.DBExceptionHandler import DBExceptionHandler
from schemas.common.Result import Result
from services.common.sql.SQLHandlerAbstract import SQLHandlerAbstract
from config.logger.LoggerConfig import get_logger

# 定义泛型类型变量
T = TypeVar('T')



class GenericSQLHandler(SQLHandlerAbstract, Generic[T]):
    """
    通用数据库处理器，支持任意 SQLAlchemy 模型和多数据库
    使用示例:
        # 使用指定数据库
        handler = GenericSQLHandler(EmailTemplate, db_name="analytics")
        # 新增（可以不传SQL，使用ORM）
        result = await handler.add_date(params={"email_template_content": "xxx"})
        # 查询、更新、删除（必须传SQL）
    """

    # 类级别的多数据库管理器，所有实例共享
    _multi_db_manager: Optional[MultiAsyncDBManager] = multi_db

    def __init__(self, model_class: Type[T], db_name: Optional[str] = None, enable_sql_log: bool = True):
        """
        初始化通用SQL处理器

        Args:
            model_class: SQLAlchemy 模型类
            db_name: 数据库名称，None表示使用默认数据库
        """
        self.model_class = model_class
        self.db_name = db_name  # 存储要使用的数据库名称
        self.table_name = model_class.__tablename__
        print(f"GenericSQLHandler 初始化完成 - 模型: {model_class.__name__}, 表: {self.table_name}, 数据库: {db_name or 'default'}")
        # 创建专门的SQL日志记录器
        self.enable_sql_log = enable_sql_log
        if self.enable_sql_log:
            self.sql_logger = get_logger(
                name=f"sql_{db_name or 'default'}",
                format_style="detailed",
                separate_error_file=True
            )

    def _log_sql_execution(self, sql: str, params: Optional[dict] = None, operation: str = "EXECUTE"):
        """记录SQL执行日志"""
        if not self.enable_sql_log:
            return

        try:
            # 格式化SQL（简单的格式化）
            formatted_sql = sql.strip().replace('\n', ' ').replace('\t', ' ')
            while '  ' in formatted_sql:
                formatted_sql = formatted_sql.replace('  ', ' ')

            self.sql_logger.info(f"[{operation}] {formatted_sql}")

            if params:
                # 过滤敏感参数
                filtered_params = {
                    k: '***' if any(sensitive in k.lower() for sensitive in ['password', 'token', 'secret']) else v
                    for k, v in params.items()
                }
                self.sql_logger.info(f"[参数] {filtered_params}")

        except Exception as e:
            self.sql_logger.warning(f"记录SQL日志失败: {e}")

    @classmethod
    def init_multi_db_manager(cls, multi_db_manager: MultiAsyncDBManager):
        """初始化多数据库管理器（应用启动时调用一次）"""
        cls._multi_db_manager = multi_db_manager

    @property
    def db_manager(self):
        """获取指定的数据库管理器"""
        if self._multi_db_manager is None:
            raise RuntimeError("多数据库管理器未初始化，请先调用 GenericSQLHandler.init_multi_db_manager()")
        return self._multi_db_manager.get_db(self.db_name)

    def _get_primary_key_name(self) -> str:
        """获取模型的主键字段名"""
        mapper = inspect(self.model_class)
        return mapper.primary_key[0].name

    @DBExceptionHandler
    async def execute(self, sql: Optional[str] = None, params: Optional[dict] = None):
        """执行自定义SQL语句"""
        if sql is None:
            return Result(code=500, message="SQL语句不能为空")

        # 记录SQL执行日志
        self._log_sql_execution(sql, params, "EXECUTE")

        async with self.db_manager.session() as session:
            result = await session.execute(text(sql), params or {})
            await session.commit()

            # 记录执行结果
            self.sql_logger.info(f"[结果] 影响行数: {result.rowcount}")

            return Result(code=200, message="SQL执行成功", data=result.rowcount)

    @DBExceptionHandler
    async def add_data(self, instance: T):
        """新增数据（使用ORM方式）"""
        if instance is None:
            return Result(code=500, message="实例不能为空")

        async with self.db_manager.session() as session:
            session.add(instance)

            # 记录ORM操作日志
            if self.enable_sql_log:
                self.sql_logger.info(f"[ORM-INSERT] 表: {self.table_name}, 模型: {self.model_class.__name__}")
                # 记录实例数据（排除敏感字段）
                instance_data = {}
                for column in inspect(self.model_class).columns:
                    value = getattr(instance, column.name, None)
                    if any(sensitive in column.name.lower() for sensitive in ['password', 'token', 'secret']):
                        instance_data[column.name] = '***'
                    else:
                        instance_data[column.name] = value
                self.sql_logger.info(f"[数据] {instance_data}")

            await session.flush()  # 刷新以获取自增ID
            pk_name = self._get_primary_key_name()
            pk_value = getattr(instance, pk_name)

            if self.enable_sql_log:
                self.sql_logger.info(f"[结果] 新增成功, {pk_name}: {pk_value}")

            return Result(
                code=200,
                message=f"新增{self.model_class.__name__}成功, {pk_name}: {pk_value}",
                data=pk_value
            )

    @DBExceptionHandler
    async def add_batch(self, instances: List[T], batch_size: Optional[int] = 1000) -> Result:
        """批量添加数据（使用模型实例列表）"""
        if not instances:
            return Result(code=400, message="实例列表不能为空")

        total_count = len(instances)
        batch_size = batch_size or 1000
        success_count = 0

        # 记录批量操作开始
        if self.enable_sql_log:
            self.sql_logger.info(
                f"[BATCH-INSERT] 开始批量插入, 表: {self.table_name}, 总数: {total_count}, 批次大小: {batch_size}")

        async with self.db_manager.session() as session:
            # 分批处理
            for i in range(0, total_count, batch_size):
                batch_instances = instances[i:i + batch_size]

                # 记录当前批次
                if self.enable_sql_log:
                    self.sql_logger.info(f"[批次 {i // batch_size + 1}] 处理 {len(batch_instances)} 条记录")

                # 批量添加到会话
                session.add_all(batch_instances)
                await session.flush()  # 刷新以获取自增ID
                success_count += len(batch_instances)

                if self.enable_sql_log:
                    self.sql_logger.info(f"[批次 {i // batch_size + 1}] 成功添加 {len(batch_instances)} 条记录")

            # 提交事务
            await session.commit()

            if self.enable_sql_log:
                self.sql_logger.info(f"[BATCH-INSERT] 批量插入完成, 成功: {success_count} 条")

            return Result(
                code=200,
                message=f"批量添加完成: 成功 {success_count} 条记录",
                data={
                    "total": total_count,
                    "success": success_count,
                    "batch_count": (total_count + batch_size - 1) // batch_size
                }
            )

    @DBExceptionHandler
    async def search_data(self, sql: Optional[str] = None, params: Optional[dict] = None, to_class: Optional[Type] = None):
        """查询数据"""
        if sql is None:
            return Result(code=500, message="SQL语句不能为空")

        # 记录查询SQL
        self._log_sql_execution(sql, params, "SELECT")

        async with self.db_manager.session() as session:
            result = await session.execute(text(sql), params or {})
            columns = result.keys()
            rows = result.fetchall()

            # 记录查询结果
            if self.enable_sql_log:
                self.sql_logger.info(f"[结果] 查询到 {len(rows)} 条记录")

            # 转换为字典列表
            data_list = [
                {column: row[i] for i, column in enumerate(columns)}
                for row in rows
            ]

            if to_class:
                data_list = await self.dicts_to_dtos(data_list, to_class)
                return Result(code=200, message="查询成功", data=data_list)
            return Result(code=200, message="查询成功", data=data_list)

    @DBExceptionHandler
    async def search_one_data(self, sql: Optional[str] = None, params: Optional[dict] = None, to_class: Optional[Type] = None, allow_none: bool = False):
        """
        查询单条数据

        Args:
            sql: SQL查询语句
            params: 查询参数
            to_class: 要转换的目标类，None表示返回字典
            allow_none: 是否允许查询结果为空，False时查询不到数据会返回错误

        Returns:
            Result: 包含单个对象的结果，而不是列表
        """
        if sql is None:
            return Result(code=500, message="SQL语句不能为空")

        # 自动添加 LIMIT 1 优化（如果SQL中没有LIMIT）
        sql_upper = sql.upper().strip()
        if 'LIMIT' not in sql_upper:
            # 正确处理分号：先去掉末尾的分号，再添加 LIMIT 1
            sql = sql.strip()
            if sql.endswith(';'):
                sql = sql[:-1]  # 去掉末尾的分号
            sql = sql + ' LIMIT 1'

        # 记录查询SQL
        self._log_sql_execution(sql, params, "SELECT_ONE")

        async with self.db_manager.session() as session:
            result = await session.execute(text(sql), params or {})
            columns = result.keys()
            rows = result.fetchall()

            # 记录查询结果
            if self.enable_sql_log:
                self.sql_logger.info(f"[结果] 查询到 {len(rows)} 条记录")

            # 处理查询结果
            if len(rows) == 0:
                if allow_none:
                    return Result(code=200, message="查询成功", data=None)
                else:
                    return Result(code=404, message="未找到数据")

            if len(rows) > 1:
                if self.enable_sql_log:
                    self.sql_logger.warning(f"[警告] 期望查询1条记录，实际查询到 {len(rows)} 条")

            # 取第一条记录
            row = rows[0]
            data_dict = {column: row[i] for i, column in enumerate(columns)}

            # 转换为指定类型
            if to_class:
                try:
                    data_obj = to_class(**data_dict)
                    return Result(code=200, message="查询成功", data=data_obj)
                except Exception as e:
                    return Result(code=500, message=f"数据转换失败: {str(e)}")

            return Result(code=200, message="查询成功", data=data_dict)

    @DBExceptionHandler
    async def update_data(self, sql: Optional[str] = None, params: Optional[dict] = None):
        """更新数据"""
        if sql is None:
            return Result(code=500, message="SQL语句不能为空")

        # 记录更新SQL
        self._log_sql_execution(sql, params, "UPDATE")

        async with self.db_manager.session() as session:
            result = await session.execute(text(sql), params or {})
            await session.commit()

            # 记录更新结果
            if self.enable_sql_log:
                self.sql_logger.info(f"[结果] 更新了 {result.rowcount} 条记录")

            return Result(
                code=200,
                message=f"成功更新{result.rowcount}条{self.model_class.__name__}记录"
            )

    @DBExceptionHandler
    async def delete_data(self, sql: Optional[str] = None, params: Optional[dict] = None):
        """删除数据"""
        if sql is None:
            return Result(code=500, message="SQL语句不能为空")

        # 记录删除SQL
        self._log_sql_execution(sql, params, "DELETE")

        async with self.db_manager.session() as session:
            result = await session.execute(text(sql), params or {})
            await session.commit()

            # 记录删除结果
            if self.enable_sql_log:
                self.sql_logger.info(f"[结果] 删除了 {result.rowcount} 条记录")

            return Result(
                code=200,
                message=f"成功删除{result.rowcount}条{self.model_class.__name__}记录"
            )

    @staticmethod
    async def dicts_to_dtos(data_list: List[dict], dto_class: Type) -> List[Any]:
        """将字典列表批量转换为 DTO 对象列表"""
        return [dto_class(**data) for data in data_list]
