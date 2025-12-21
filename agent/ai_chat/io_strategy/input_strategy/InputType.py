from enum import Enum


class InputType(Enum):
    """
    输入类型枚举
    """
    TEXT = "text"
    VOICE = "voice"
    # 文件与文字
    # FILE_AND_TEXT = "file_and_text"