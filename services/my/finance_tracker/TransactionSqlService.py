from typing import Optional, List
from model.finance_tracker.Transaction import Transaction
from services.common.sql.GenericSQLHandler import GenericSQLHandler


class TransactionSqlService(GenericSQLHandler[Transaction]):

    def __init__(self, db_name: Optional[str] = "finance_db"):
        super().__init__(Transaction, db_name=db_name, enable_sql_log=False)

    async def add_one_transaction(self, transaction: Transaction) -> Transaction:
        """
        添加一条流水记录
        :param transaction: 流水记录
        :return: 流水记录
        """
        return await self.add_one_data(transaction)

    async def search_user_transactions_by_time(self, user_id: int, start_time: str, end_time: str) -> List[Transaction]:
        """
        根据用户ID和时间范围查询流水记录
        :param user_id: 用户ID
        :param start_time: 开始时间
        :param end_time: 结束时间
        :return: 流水记录列表
        """
        sql = """
        SELECT * FROM transactions WHERE user_id = :user_id AND transaction_time >= :start_time AND transaction_time <= :end_time;
        """
        return await self.search_data(sql=sql, params={"user_id": user_id, "start_time": start_time, "end_time": end_time})

    async def alter_transaction_by_id(self, transaction_id: int, transaction: Transaction) -> Transaction:
        """
        根据ID更新流水记录
        :param transaction_id: 流水ID
        :param transaction: 更新的流水记录
        :return: 更新后的流水记录
        """
        sql = """
        UPDATE transactions SET amount = :amount, type = :type, transaction_time = :transaction_time, remark = :remark WHERE transaction_id = :transaction_id;
        """
        return await self.update_data(sql=sql, params={"amount": transaction.amount, "type": transaction.type, "transaction_time": transaction.transaction_time, "remark": transaction.remark, "transaction_id": transaction_id})

    # noinspection PyMethodMayBeStatic
    async def delete_transaction_by_id(self, transaction_id: int):
        """
        根据ID删除流水记录(逻辑删除)
        :param transaction_id: 流水ID
        :return: 删除的流水记录
        """
        pass




