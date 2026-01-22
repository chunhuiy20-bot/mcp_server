from pydantic import BaseModel

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

# 请求参数
class GetHistoryChatRequest(BaseModel):
    deviceId: str


# 语音对话数据模型
class AgentChatHistoryDTO(BaseModel):

    created_at: datetime = Field(..., alias="createdAt", description="创建时间")
    chat_type: int = Field(..., alias="chatType", description="消息类型: 1-用户, 2-智能体")
    content: str = Field(..., description="聊天内容")
    audio_id: Optional[str] = Field(None, alias="audioId", description="音频ID")
    mac_address: Optional[str] = Field(None, alias="macAddress", description="MAC地址")

    class Config:
        # 支持驼峰命名和下划线命名的自动转换
        populate_by_name = True
        # 定义字段别名，支持 JSON 序列化时使用驼峰命名
        json_schema_extra = {
            "example": {
                "created_at": "2026-01-22T11:52:00",
                "chat_type": 1,
                "content": "你好",
                "audio_id": "audio_123",
                "mac_address": "00:1B:44:11:3A:B7"
            }
        }


# 用户聊天历史数据存储模型
class UserChatHistoryDto(BaseModel):
    """用户测试数据传输对象"""

    user_id: str = Field(..., alias="userId", description="用户ID")
    chat_history_list: List[AgentChatHistoryDTO] = Field(..., alias="chatHistoryList", description="聊天记录列表")

    class Config:
        populate_by_name = True
