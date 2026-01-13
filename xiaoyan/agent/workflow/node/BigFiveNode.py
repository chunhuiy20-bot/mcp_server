# 每一个由一个小智能体构建而成
from agent.ai_chat.AIChatAbstract import AIChatAbstract
from agent.react_agent.ReactAgentBuilder import ReactAgentBuilder
from xiaoyan.agent.workflow.node.NodeAbstract import NodeAbstract
from xiaoyan.agent.workflow.prompt.PersonaConstructorWorkflowAllPrompt import PersonaConstructorWorkflowAllPromptEN
from xiaoyan.rpc.XiaoYanRPCClient import xiao_yan_api_rpc_client
from xiaoyan.rpc.rpc_schemas.XiaoYanVo import ChatMessage


class BigFiveNode(NodeAbstract[list[ChatMessage]]):

    def __init__(self):
        self.client: AIChatAbstract | None = None

    async def _ensure_client(self):
        if self.client is None:
            self.client = await (ReactAgentBuilder(agent_name=PersonaConstructorWorkflowAllPromptEN[1]["name"]).
                                 with_system_prompt(PersonaConstructorWorkflowAllPromptEN[1]["content"]).
                                 build("1008611"))

    async def run_node(self, input_data: list[ChatMessage], **kwargs) -> str:
        await self._ensure_client()
        chat_history = "\n\n".join([
            f"{msg.role}: {msg.content}"
            for msg in input_data
        ])
        big_five_result = await self.client.chat(user_input=chat_history)
        return big_five_result



async def main():
    bigfivenode = BigFiveNode()
    result = await xiao_yan_api_rpc_client.get_history_chat()
    res = await bigfivenode.run_node(result.data.history_chat_list[0].chat_history)
    print(res)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())