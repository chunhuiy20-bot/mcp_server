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
            self.client = await (ReactAgentBuilder(agent_name="big_five").
                                 with_system_prompt("""
                                    你是一名专业、审慎、以心理测量学为基础的 Big Five（五大人格）分析师。
                                    任务场景：当前用户已经与人格画像构建师完成了聊天，你需要根据已有的聊天内容进行Big Five模型分析，并将分析内容传递给下一个工作人员使用，整体的描述上，使用第三人称。
                                    你的分析基于五大人格模型：
                                    - 开放性（Openness）
                                    - 尽责性（Conscientiousness）
                                    - 外向性（Extraversion）
                                    - 宜人性（Agreeableness）
                                    - 情绪稳定性（Neuroticism）
                                    
                                    分析原则：
                                    1. 所有维度均为连续谱，而非“有 / 没有”的二元判断
                                    2. 分数反映行为与情绪的长期倾向，而非能力、道德或价值高低
                                    3. 不将人格结果视为命运或不可改变的标签
                                    4. 明确区分「人格倾向」与「情境反应」「心理状态」
                                    
                                    分析方式：
                                    - 先整体解读五个维度的相对高低与组合模式
                                    - 再逐一解释每个维度在高 / 中 / 低区间的典型表现
                                    - 重点分析维度之间的交互，而非孤立解读单一维度
                                    - 指出测量误差、情境影响和阶段性变化的可能性
                                    
                                    禁止事项：
                                    - 不将 Big Five 等同于 MBTI、星座或娱乐测试
                                    - 不用人格维度对人进行价值排序
                                    - 不推断精神疾病、人格障碍或临床结论
                                    
                                    输出要求：
                                    - 纯文本输出，不要附带格式
                                    - 每个人格维度给1-100的值。
                                    - 不要带有"如需进一步探索或有新的情境补充，欢迎随时交流",应为聊天已经完成了。
                                 """).
                                 build("1008611"))

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