# 将多个节点编译成图/工作流
import asyncio

from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Any
import operator

from langgraph.graph.state import CompiledStateGraph

from schemas.common.Result import Result
from schemas.ybbl.ai_school.vo.PersonalityReportVo import TalentReportResponse
from xiaoyan.agent.workflow.node.BigFiveNode import BigFiveNode
from xiaoyan.agent.workflow.node.CliftonStrengthsNode import CliftonStrengthsNode
from xiaoyan.agent.workflow.node.MBTINode import MBTINode
from xiaoyan.agent.workflow.node.PersonaConstructorNode import PersonaConstructorNode
from xiaoyan.rpc.XiaoYanRPCClient import xiao_yan_api_rpc_client
from xiaoyan.rpc.rpc_schemas.XiaoYanVo import ChatMessage, UserHistoryChatList


class PersonaConstructorWorkflow:
    """人格画像构建工作流"""

    class State(TypedDict, total=False):
        """工作流状态定义"""
        user_history_chat_list: list[ChatMessage]
        analysis_results: Annotated[list, operator.add]  # 累积三个分析结果
        final_report: TalentReportResponse
        user_id: str

    def __init__(self):
        """初始化工作流和各个节点"""
        self.big_five_node = BigFiveNode()
        self.mbti_node = MBTINode()
        self.clifton_node = CliftonStrengthsNode()
        self.persona_constructor_node = PersonaConstructorNode()

        # 构建图
        self.app = self._build_graph()

        # rpc远程调用客户端
        self.xiao_yan_api_rpc_client = xiao_yan_api_rpc_client


    def _build_graph(self) -> CompiledStateGraph:
        """构建 LangGraph 工作流图"""
        workflow = StateGraph(self.State)

        # 添加节点
        workflow.add_node("start", self._start_node)
        workflow.add_node("big_five", self._big_five_analysis)
        workflow.add_node("mbti", self._mbti_analysis)
        workflow.add_node("clifton", self._clifton_analysis)
        workflow.add_node("integration", self._final_integration)

        # 设置入口点
        workflow.set_entry_point("start")

        # 从 start 并行分发到三个分析节点
        workflow.add_edge("start", "big_five")
        workflow.add_edge("start", "mbti")
        workflow.add_edge("start", "clifton")

        # 三个分析节点都流向整合节点
        workflow.add_edge("big_five", "integration")
        workflow.add_edge("mbti", "integration")
        workflow.add_edge("clifton", "integration")

        # 整合节点完成后结束
        workflow.add_edge("integration", END)

        return workflow.compile()

    # noinspection PyMethodMayBeStatic
    async def _start_node(self, state: State) -> State:
        """起始节点 - 初始化"""
        print(f"开始人格分析工作流...{state}")
        return {"analysis_results": []}

    async def _big_five_analysis(self, state: State) -> State:
        """Big Five 分析节点"""
        print("执行 Big Five 分析...")
        result = await self.big_five_node.run_node(state['user_history_chat_list'])
        return {"analysis_results": [result]}

    async def _mbti_analysis(self, state: State) -> State:
        """MBTI 分析节点"""
        print("执行 MBTI 分析...")
        result = await self.mbti_node.run_node(state['user_history_chat_list'])
        return {"analysis_results": [result]}

    async def _clifton_analysis(self, state: State) -> State:
        """盖洛普优势分析节点"""
        print("执行盖洛普优势分析...")
        result = await self.clifton_node.run_node(state['user_history_chat_list'])
        return {"analysis_results": [result]}

    async def _final_integration(self, state: State) -> State:
        """最终整合节点"""
        print("整合分析结果...")
        print(f"当前累积结果: {state['analysis_results']}")
        final_report = await self.persona_constructor_node.run_node(state['analysis_results'])
        return {"final_report": final_report}

    async def run(self, user_history_chat_list: Any, user_id: str) -> Result[TalentReportResponse]:
        """
        运行工作流

        Args:
            user_history_chat_list: 单个用户聊天历史
            user_id: 用户唯一标识符

        Returns:
            TalentReportResponse: 最终人格分析报告
        """
        try:
            initial_state = {
                "user_history_chat_list": user_history_chat_list,
                "analysis_results": [],
                "final_report": None,
                "user_id": user_id
            }

            result = await self.app.ainvoke(initial_state)
            report: TalentReportResponse = result['final_report']
            report.user_id = user_id
            return Result(data=report)
        except Exception as e:
            return Result(code=500, message=f"执行工作流失败: {e}", data=user_id)

    async def report_scheduled_Task(self):
        result: Result[UserHistoryChatList] = await self.xiao_yan_api_rpc_client.get_history_chat()
        if result.code != 200 and result.code != 0:
            # 获取聊天记录失败，无需后续逻辑
            return result
        if len(result.data.history_chat_list) <= 0:
            # 聊天记录为空，无需后续逻辑
            return result

        print(f"获取到 {len(result.data.history_chat_list)} 个用户的聊天记录，开始并行处理...")

        # 并行处理所有用户的聊天记录
        tasks = [
            self.run(user_history_chat_list=user_chat.chat_history, user_id=user_chat.user_id)
            for user_chat in result.data.history_chat_list
        ]

        # 等待所有任务完成
        report_results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        success_count = 0
        failed_count = 0

        print(f"处理结果:{report_results}")
        for result_report in report_results:
            if result_report.code == 200:
                success_count += 1
                # 调用 xiao_yan_api_rpc_client 保存报告
                print(await self.xiao_yan_api_rpc_client.submit_user_profile(result_report.data))
            else:
                failed_count += 1



        return Result(data={
                "total": len(result.data.history_chat_list),
                "success": success_count,
                "failed": failed_count,
                "reports": [r for r in report_results if not isinstance(r, Exception)]
            }
        )


persona_constructor_workflow = PersonaConstructorWorkflow()
