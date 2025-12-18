from sqlalchemy import Column, String, Text, BigInteger, DateTime, func, Integer, Numeric
from sqlalchemy.ext.declarative import declarative_base
from model.BaseEntity import BaseEntity


class ToolSet(BaseEntity):
    __tablename__ = "tool_sets"

    project_id = Column(BigInteger, nullable=True, comment='项目id')
    tool_category_name = Column(String(50), nullable=True, comment='工具集名称')
    tool_name = Column(String(50), nullable=True, comment='工具名称')
    description = Column(String(200), nullable=True, comment='工具描述')
    running_status = Column(Integer, default=1, nullable=True, comment='运行状态（0：异常 1：正常运行）')

    def __repr__(self):
        return f"<ToolSet(id={self.id}, project_id={self.project_id}, tool_category_name={self.tool_category_name}, tool_name={self.tool_name}, description={self.description}, running_status={self.running_status}...)>"

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'tool_category_name': self.tool_category_name,
            'tool_name': self.tool_name,
            'description': self.description,
            'running_status': self.running_status,
            'create_time': self.create_time.isoformat() if self.create_time else None,
        }




# 测试
# tool_set = ToolSet(project_id=20240510, tool_category_name="ToolSet", tool_name="ToolSet", description="ToolSet")
# print(tool_set.to_dict())