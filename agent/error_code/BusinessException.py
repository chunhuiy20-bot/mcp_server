from agent.error_code.AiBussnessErrorCode import AIBusinessErrorCode
from typing import Optional, Any


class BusinessException(Exception):
    """业务异常基类"""

    def __init__(
            self,
            error_code: AIBusinessErrorCode,
            detail: Optional[str] = None,
            data: Optional[Any] = None
    ):
        self.error_code = error_code
        self.code = error_code.code
        self.message = error_code.message
        self.detail = detail
        self.data = data

        # 构建完整错误信息
        full_message = f"[{self.code}] {self.message}"
        if detail:
            full_message += f": {detail}"

        super().__init__(full_message)

    def to_dict(self):
        """转换为字典格式，方便API返回"""
        result = {
            "code": self.code,
            "message": self.message,
        }
        if self.detail:
            result["detail"] = self.detail
        if self.data:
            result["data"] = self.data
        return result

    def __str__(self):
        return f"BusinessException(code={self.code}, message={self.message}, detail={self.detail})"