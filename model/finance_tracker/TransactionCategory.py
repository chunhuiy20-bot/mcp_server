from sqlalchemy import Column, Integer, String

from model.BaseEntity import BaseEntity


class TransactionCategory(BaseEntity):
    __tablename__ = 'transaction_category'
    transaction_category_id = Column(Integer, primary_key=True, comment='流水分类ID')
    transaction_category_name = Column(String(50), nullable=True, comment='流水分类名称')
    transaction_category_type = Column(Integer, nullable=True, comment='流水分类类型（1：支出 2：收入）')
    transaction_category_icon_url = Column(String(255), nullable=True, comment='流水分类图标URL')
    is_user_defined = Column(Integer, nullable=True, comment='是否是用户自定义的分类（不是的时候为0.是的时候填写用户id）')
