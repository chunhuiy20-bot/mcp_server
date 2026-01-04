from pydantic import BaseModel


# 请求参数
class GetHistoryChatRequest(BaseModel):
    deviceId: str




