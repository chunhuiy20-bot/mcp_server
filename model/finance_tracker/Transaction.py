from sqlalchemy import Column, Integer, Float, DateTime

from model.BaseEntity import BaseEntity


class Transaction(BaseEntity):
    __tablename__ = 'transaction'

    user_id = Column(Integer, nullable=True, comment='用户ID')
    transaction_name = Column(Integer, nullable=True, comment='交易流水名称')
    transaction_time = Column(DateTime, nullable=True, comment='交易时间')
    transaction_amount = Column(Float, nullable=True, comment='金额')
    transaction_category_id = Column(Integer, nullable=True, comment='流水分类ID')
    transaction_type = Column(Integer, nullable=True, comment='交易分类（1：支出 2：收入）')
    transaction_remark = Column(Integer, nullable=True, comment='备注')

    def __repr__(self):
        return f'<Transaction(id={self.id}, user_id={self.user_id}, transaction_name={self.transaction_name}, transaction_time={self.transaction_time}, transaction_amount={self.transaction_amount}, transaction_category_id={self.transaction_category_id}, transaction_type={self.transaction_type}, transaction_remark={self.transaction_remark})>'


    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'transaction_name': self.transaction_name,
            'transaction_time': self.transaction_time,
            'transaction_amount': self.transaction_amount,
            'transaction_category_id': self.transaction_category_id,
            'transaction_type': self.transaction_type,
            'transaction_remark': self.transaction_remark
        }


transaction = Transaction(user_id=1, transaction_name="测试", transaction_time="2023-01-01 00:00:00", transaction_amount=100.00, transaction_category_id=1, transaction_type=1, transaction_remark="测试")
print(transaction.to_dict())
