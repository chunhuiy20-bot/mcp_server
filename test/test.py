from collections import defaultdict
from datetime import date, datetime
from typing import List, Optional
from config.logger.LoggerConfig import api_log
from model.test.FoodData import FoodData
from model.test.ToolSet import ToolSet
from services.common.sql.GenericSQLHandler import GenericSQLHandler


class FoodDataSqlService(GenericSQLHandler[FoodData]):

    def __init__(self, db_name: Optional[str] = "main"):
        """
        初始化食物数据服务

        Args:
            db_name: 数据库名称，None表示使用默认数据库
                    可选值: "main", "nutrition", "analytics" 等
        """
        super().__init__(FoodData, db_name=db_name, enable_sql_log=False)

    # @api_log(logger_name="food_data_service", log_result=True)
    async def select_food_data(self, user_id: int):
        """
        添加食物数据
        :param user_id:
        :return: 食物数据
        """
        sql = """
        SELECT * FROM food_data WHERE user_id = :user_id;
        """
        result = await self.search_one_data(sql=sql, params={"user_id": user_id}, to_class=FoodData)
        return result


class ToolSetSqlService(GenericSQLHandler[ToolSet]):
    def __init__(self, db_name: Optional[str] = "db2"):
        """
        初始化工具集服务

        Args:
            db_name: 数据库名称，None表示使用默认数据库
                    可选值: "main", "nutrition", "analytics" 等
        """
        super().__init__(ToolSet, db_name=db_name)

    async def select_tool_set(self):
        """
        查询工具集
        :return: 工具集
        """
        sql = """
        SELECT * FROM tool_sets;
        """
        return await self.search_data(sql=sql, params=None)


async def main():
    food_data_sql_service = FoodDataSqlService()
    result = await food_data_sql_service.select_food_data(user_id=1993600382818562050)
    print(result)
    # tool_set_sql_service = ToolSetSqlService()
    # result = await tool_set_sql_service.select_tool_set()
    # print(result)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())