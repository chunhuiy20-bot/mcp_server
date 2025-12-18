from pydantic import Field, ConfigDict

from schemas.common.Result import Result


class ToolVo(Result):
    type: int = Field(default=1000, description="工具返回数据类型")
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    @classmethod
    def from_result(cls, result: Result, type: int = 1000):
        return cls(**result.model_dump(), type=type)

    def to_result(self) -> Result:
        """将 ToolVo 转回 Result"""
        return Result(**self.model_dump(exclude={"type"}))

