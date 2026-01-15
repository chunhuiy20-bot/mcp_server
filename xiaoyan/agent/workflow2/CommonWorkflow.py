from typing import Literal, Dict, Type, Any
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel
from agent.workflow.workflow_orchestration.workflow_compiler.WorkflowGraphCompiler import WorkflowGraphCompiler
from agent.workflow.workflow_orchestration.workfolw_config_loader.WorkflowConfigLoader import WorkflowConfigLoader
from xiaoyan.rpc.XiaoYanRPCClient import xiao_yan_api_rpc_client


class CreateWorkflowDto(BaseModel):
    config_type: Literal["file", "json_string"]
    config: str


class CommonWorkflow:
    """
    通用工作流
    """
    def __init__(self):
        # 工作流配置加载器
        self.workflow_config_loader = WorkflowConfigLoader()
        # 工作流缓存区域
        self.workflow_cache: Dict[str, Type[CompiledStateGraph]] = {}

    async def _create_workflow(self, create_workflow_dto: CreateWorkflowDto) -> CompiledStateGraph:
        """
        依靠配置简单创建工作流实例
        使用工作就编译器加载工作流配置加载器的config来创建工作流
        :return:
        """
        if create_workflow_dto.config_type == "file":
            config = self.workflow_config_loader.load_from_file(create_workflow_dto.config)
            print(config)
            return await WorkflowGraphCompiler(config).compile()
        else:
            config = self.workflow_config_loader.load_from_string(create_workflow_dto.config)
            print(config)
            return await WorkflowGraphCompiler(config).compile()

    async def create_workflow(self, create_workflow_dto: CreateWorkflowDto):
        """
        返回工作流
        :return:
        """
        workflow = await self._create_workflow(create_workflow_dto)
        return workflow

    @staticmethod
    async def run_workflow(cls, workflow: CompiledStateGraph, user_input: Any):
        return await workflow.ainvoke(user_input)

    async def save_workflow(self, unique: str):
        """
        缓存工作流到缓存区域
        :return bool
        """
        pass

    async def get_workflow(self, unique: str):
        """
        从缓存区域获取工作流实例 # todo 可以放到redis
        :return workflow实例
        """
        pass


common_workflow = CommonWorkflow()


async def test():
    create_workflow_dto = CreateWorkflowDto(config_type="file", config="persona_constructor_workflow.json")
    workflow = await common_workflow.create_workflow(create_workflow_dto)
    result = await xiao_yan_api_rpc_client.get_history_chat()
    print(f"Code: {result.code}")
    print(f"Message: {result.message}")
    print(f"用户数量: {len(result.data.history_chat_list)}")
    print(result.data.history_chat_list[0].chat_history)
    # 打印每个用户的聊天记录
    for user_chat in result.data.history_chat_list:
        print(f"\n用户ID: {user_chat.user_id}")
        print(f"聊天记录数: {len(user_chat.chat_history)}")
        # for msg in user_chat.chat_history[:-3]:  # 只打印前3条
            # print(f" {msg.role}: {msg.content}")

    mock_chat_history = result.data.history_chat_list[0].chat_history
    user_input = {
        "user_history_chat_list": mock_chat_history,
        "analysis_results": [],
        "final_report": None,
        "user_id": "test_user_001"
    }
    result = await workflow.ainvoke(user_input)
    print(result['final_report'])

if __name__ == "__main__":
    import asyncio
    asyncio.run(test())
