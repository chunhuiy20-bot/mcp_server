# 每一个由一个小智能体构建而成
from agent.AIChatAbstract import AIChatAbstract
from agent.react_agent.ReactAgentBuilder import ReactAgentBuilder
from xiaoyan.rpc.XiaoYanRPCClient import xiao_yan_api_rpc_client
from xiaoyan.rpc.rpc_schemas.XiaoYanVo import UserHistoryChatList


class BigFiveNode:

    def __init__(self):
        self.client: AIChatAbstract | None = None

    async def _ensure_client(self):
        if self.client is None:
            self.client = await ReactAgentBuilder(agent_name="big_five").with_system_prompt("你是mbti分析大师，根据用户与人格画像构建师的聊天内容分析用户的mbti，并给出详细的解释").build("1008611")

    async def summary_big_five_test(self,user_history_chat_list: UserHistoryChatList)-> str:
        await self._ensure_client()
        chat_history = "\n\n".join([
            f"{msg.role}: {msg.content}"
            for msg in user_history_chat_list
        ])
        big_five_result = await self.client.chat(user_input=chat_history)
        return big_five_result



async def main():
    bigfivenode = BigFiveNode()
    result = await xiao_yan_api_rpc_client.get_history_chat()
    res = await bigfivenode.summary_big_five_test(result.data.history_chat_list[0].chat_history)
    print(res)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())