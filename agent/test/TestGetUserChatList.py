import requests
from pydantic import BaseModel
from schemas.common.Result import Result
from typing import Literal
from schemas.ybbl.ai_school.vo.PersonalityReportVo import TalentReportResponse


class GetHistoryChatRequest(BaseModel):
    deviceId: str


class ChatMessage(BaseModel):
    role: Literal["用户", "人格画像构建师"]
    content: str


class GetHistoryChatResponse(BaseModel):
    user_id: str
    chat_history: list[ChatMessage]


class UserHistoryChatList(BaseModel):
    history_chat_list: list[GetHistoryChatResponse]


class XiaoZhiAPIClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    async def get_history_chat(self, request: GetHistoryChatRequest | None = None) -> Result[UserHistoryChatList]:
        url = f"{self.base_url}/xiaozhi/we1yess/getHistoryChat"
        payload = request.model_dump(by_alias=True) if request else {}
        response = requests.post(
            url,
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()

        result = response.json()

        # 处理返回数据
        history_chat_list = []

        # 遍历 data 中的每个用户
        for user_id, chat_list in result.get('data', {}).items():
            chat_history = []

            # 转换每条聊天记录
            for chat in chat_list:
                role = "用户" if chat['chatType'] == 1 else "人格画像构建师"
                chat_history.append(ChatMessage(
                    role=role,
                    content=chat['content']
                ))

            history_chat_list.append(GetHistoryChatResponse(
                user_id=user_id,
                chat_history=chat_history
            ))

        # 构建最终结果
        user_history_chat_list = UserHistoryChatList(history_chat_list=history_chat_list)

        return Result(
            code=result['code'],
            message=result['msg'],
            data=user_history_chat_list
        )

    async def submit_user_profile(self, profile: TalentReportResponse) -> Result:
        """提交用户画像到后端"""
        url = f"{self.base_url}/xiaozhi/we1yess/analyze-profile"

        # by_alias=True 会自动将 snake_case 转换为 camelCase
        payload = profile.model_dump(by_alias=True, exclude_none=True)

        response = requests.post(
            url,
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()

        result = response.json()
        return Result(
            code=result.get('code'),
            msg=result.get('msg'),
            data=result.get('data')
        )


# 使用
xiao_zhi_api_client = XiaoZhiAPIClient(
    base_url="http://47.107.82.252:8002",
    token="2a315992-6278-4bfb-ad34-62644953a725"
)


async def main():
    result = await xiao_zhi_api_client.get_history_chat()
    print(f"Code: {result.code}")
    print(f"Message: {result.message}")
    print(f"用户数量: {len(result.data.history_chat_list)}")

    # 打印每个用户的聊天记录
    for user_chat in result.data.history_chat_list:
        print(f"\n用户ID: {user_chat.user_id}")
        print(f"聊天记录数: {len(user_chat.chat_history)}")
        for msg in user_chat.chat_history:  # 只打印前3条
            print(f" {msg.role}: {msg.content}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
