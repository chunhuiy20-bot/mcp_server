# 汇聚其他智能体的结果，进一步分析并最终输出结构化数据
from openai import AsyncOpenAI
from dotenv import load_dotenv
from schemas.ybbl.ai_school.vo.PersonalityReportVo import TalentReportResponse
from xiaoyan.agent.workflow.node.NodeAbstract import NodeAbstract
from xiaoyan.agent.workflow.prompt.PersonaConstructorWorkflowAllPrompt import PersonaConstructorWorkflowAllPromptEN
from xiaoyan.rpc.XiaoYanRPCClient import xiao_yan_api_rpc_client
import os
load_dotenv()


class PersonaConstructorNode(NodeAbstract[list[str]]):

    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"),base_url=os.getenv("OPENAI_BASE_URL"))

    async def _ensure_client(self):
        if self.client is None:
            self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"),base_url=os.getenv("OPENAI_BASE_URL"))

    async def run_node(self, report: list[str], **kwargs) -> TalentReportResponse:
        await self._ensure_client()
        response = await self.client.chat.completions.parse(
            model="gpt-4.1",  # 建议使用 gpt-4-turbo 或 gpt-4o 以保证 JSON 结构的稳定性
            messages=[
                {"role": "system", "content": PersonaConstructorWorkflowAllPromptEN[4]["content"]},
                {"role": "user", "content": f"一下是三分独立专业分析报告：\n\n{report}"}
            ],
            response_format=TalentReportResponse,
            temperature=0.3  # 保持一定的创造性，但在结构上受控
        )
        # 获取解析后的 Pydantic 对象
        report_data: TalentReportResponse = response.choices[0].message.parsed
        return report_data


async def main():
    bigfivenode = PersonaConstructorNode()
    result = await xiao_yan_api_rpc_client.get_history_chat()
    res = await bigfivenode.run_node(result.data.history_chat_list[0].chat_history)
    print(res)



if __name__ == "__main__":
    import asyncio

    asyncio.run(main())