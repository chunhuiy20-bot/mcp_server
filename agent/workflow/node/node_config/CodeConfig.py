from dataclasses import dataclass


@dataclass
class CodeConfig:
    custom_code: str = None  # 自定义代码, 自动执行
