"""
workflow配置加载器
功能：1、从字符串中，将有json结构的配置数据加载为配置类 (不推荐)
     2、从字典中加载工作流的配置类 (推荐)
     3、从json配置文件加载工作流的配置类 (强烈推荐)
     4、检查构建的配置类是否符合规范
"""
import json
import asyncio
from pathlib import Path
from typing import Union, List

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver

from agent.workflow.workflow_orchestration.WorkflowGraphCompiler import GraphConfig, WorkflowGraphCompiler


class WorkflowConfigLoader:
    """工作流配置加载器"""

    @staticmethod
    def load_from_file(file_path: Union[str, Path]) -> GraphConfig:
        """从 JSON 文件加载配置"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {file_path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return WorkflowConfigLoader._parse_config(data)

    @staticmethod
    def load_from_dict(data: dict) -> GraphConfig:
        """从字典加载配置"""
        return WorkflowConfigLoader._parse_config(data)

    @staticmethod
    def load_from_string(json_string: str) -> GraphConfig:
        """从 JSON 字符串加载配置"""
        data = json.loads(json_string)
        return WorkflowConfigLoader._parse_config(data)

    @staticmethod
    def _parse_config(data: dict) -> GraphConfig:
        """解析配置"""
        required_fields = ["name", "state_schema", "nodes", "edges", "entry_point"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"配置缺少必要字段: {field}")

        return GraphConfig(
            name=data["name"],
            description=data.get("description", ""),
            state_schema=data["state_schema"],
            nodes=data["nodes"],
            edges=data["edges"],
            entry_point=data["entry_point"]
        )

    @staticmethod
    def validate_config(config: GraphConfig) -> List[str]:
        """验证配置，返回错误列表"""
        errors = []
        node_names = {node["name"] for node in config.nodes}

        # 检查入口点
        if config.entry_point not in node_names:
            errors.append(f"入口点 '{config.entry_point}' 不在节点列表中")

        # 检查边的节点引用
        for edge in config.edges:
            source = edge.get("source")
            if source not in node_names:
                errors.append(f"边的源节点 '{source}' 不存在")

            if edge.get("type") == "normal":
                target = edge.get("target")
                if target != "END" and target not in node_names:
                    errors.append(f"边的目标节点 '{target}' 不存在")

            elif edge.get("type") == "conditional":
                for target in edge.get("condition_map", {}).values():
                    if target != "END" and target not in node_names:
                        errors.append(f"条件边的目标节点 '{target}' 不存在")

        return errors


async def main():
    # 加载配置
    config = WorkflowConfigLoader.load_from_file("workflow_config.json")

    # 验证配置
    errors = WorkflowConfigLoader.validate_config(config)
    if errors:
        for err in errors:
            print(f"配置错误: {err}")
        return

    # 编译并运行
    compiler = WorkflowGraphCompiler(config)
    checkpointer = InMemorySaver()
    graph = await compiler.compile(checkpointer=checkpointer)
    thread_config: RunnableConfig = {"configurable": {"thread_id": "1"}}
    result = await graph.ainvoke({
        "messages": [{"role": "user", "content": "北京今天天气怎么样？"}],
        "intent": "",
        "output": ""
    }, config=thread_config)
    print(f"结果: {result}")
    result2 = await graph.ainvoke({
        "messages": [{"role": "user", "content": "我上一个问题是什么"}],
        "intent": "",
        "output": ""
    }, config=thread_config)
    print(f"结果: {result2}")


async def main2():
    # 加载配置
    config = WorkflowConfigLoader.load_from_file("workflow_config2.json")

    # 验证配置
    errors = WorkflowConfigLoader.validate_config(config)
    if errors:
        for err in errors:
            print(f"配置错误: {err}")
        return

    # 编译
    compiler = WorkflowGraphCompiler(config)
    graph = await compiler.compile()

    # 模拟用户聊天历史数据
    mock_chat_history = [
        {"role": "assistant", "content": "你好！我是人格画像探索向导。能分享一个最近让你印象深刻的事件吗？"},
        {"role": "user",
         "content": "上周我们团队做了一个紧急项目，我主动承担了协调各方的工作，虽然压力很大但最后按时完成了。"},
        {"role": "assistant", "content": "听起来你在压力下表现得很出色！在协调过程中，你是怎么处理不同意见的？"},
        {"role": "user",
         "content": "我会先听完每个人的想法，然后找出共同点，再提出一个综合方案。如果有人坚持己见，我会私下沟通。"},
        {"role": "assistant", "content": "你很注重团队和谐。那在做决策时，你更依赖数据分析还是直觉？"},
        {"role": "user", "content": "我更喜欢先收集数据，但最终决策时也会考虑团队成员的感受。"},
        {"role": "assistant", "content": "面对突发变化时，你通常怎么应对？"},
        {"role": "user",
         "content": "说实话我不太喜欢突发情况，我更喜欢提前规划好一切。但如果真的发生了，我会快速调整计划。"},
        {"role": "assistant", "content": "你对学习新技能有什么看法？"},
        {"role": "user", "content": "我很喜欢学习新东西，尤其是能提升工作效率的技能。我每周都会抽时间看专业书籍。"}
    ]

    # 运行工作流
    result = await graph.ainvoke({
        "user_history_chat_list": mock_chat_history,
        "analysis_results": [],
        "final_report": None,
        "user_id": "test_user_001"
    })

    print("=" * 50)
    print("工作流执行完成")
    print("=" * 50)

    print(result)
    # 查看结果
    if "final_report" in result:
        print(f"最终报告: {result['final_report']}")


async def main3():
    config = WorkflowConfigLoader.load_from_string("""
    {
      "name": "chat_workflow",
      "description": "智能对话工作流",
      "state_schema": {
        "messages": {"type": "list", "reducer": "add"},
        "intent": {"type": "str"},
        "output": {"type": "str"}
      },
      "entry_point": "intent_classifier",
      "nodes": [
        {
          "name": "intent_classifier",
          "type": "llm",
          "config": {
            "system_prompt": "分析用户意图，只返回以下类型之一: question, chat, task",
            "model": "gpt-4.1",
            "temperature": 0.0,
            "need_structure_output": true,
            "output_schema": {
              "intent": {"type": "str", "description": "意图类型: question/chat/task"}
            }
          }
        },
        {
          "name": "question_handler",
          "type": "llm",
          "config": {
            "system_prompt": "你是一个知识问答助手，准确回答用户问题",
            "model": "gpt-4.1",
            "temperature": 0.3
          }
        },
        {
          "name": "chat_handler",
          "type": "llm",
          "config": {
            "system_prompt": "你是一个友好的聊天助手，轻松愉快地与用户交流",
            "model": "gpt-4.1",
            "temperature": 0.7
          }
        },
        {
          "name": "task_handler",
          "type": "code",
          "config": {
            "custom_code": "result = {'output': '任务已收到，正在处理中...'}"
          }
        }
      ],
      "edges": [
        {
          "type": "conditional",
          "source": "intent_classifier",
          "condition_field": "intent",
          "condition_map": {
            "question": "question_handler",
            "chat": "chat_handler",
            "task": "task_handler"
          },
          "default": "chat_handler"
        },
        {"type": "normal", "source": "question_handler", "target": "END"},
        {"type": "normal", "source": "chat_handler", "target": "END"},
        {"type": "normal", "source": "task_handler", "target": "END"}
      ]
    }
    """)
    errors = WorkflowConfigLoader.validate_config(config)
    print(config)



if __name__ == "__main__":
    import asyncio
    asyncio.run(main2())
