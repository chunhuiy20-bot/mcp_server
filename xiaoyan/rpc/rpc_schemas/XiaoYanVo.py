from pydantic import BaseModel
from typing import Literal


# 将数据处理成我需要的结构
class ChatMessage(BaseModel):
    role: str
    content: str


class GetHistoryChatResponse(BaseModel):
    user_id: str
    chat_history: list[ChatMessage]


class UserHistoryChatList(BaseModel):
    history_chat_list: list[GetHistoryChatResponse]