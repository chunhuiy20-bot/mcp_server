from typing import Optional, Any, Dict, List
from langgraph.graph import StateGraph, END
from agent.workflow.node.UniversalNode import UniversalNode
from agent.workflow.node.UniversalNodeBuilder import UniversalNodeBuilder
from agent.workflow.node.node_config.CodeConfig import CodeConfig
from agent.workflow.node.node_config.LLMConfig import LLMConfig
from langchain_core.messages import AIMessage
from agent.workflow.workflow_orchestration.workflow_config.GraphConfig import GraphConfig


# ============ 图编译器 ============
class WorkflowGraphCompiler:
    """配置驱动的图编译器"""

    def __init__(self, config: GraphConfig):
        self.config = config
        self._nodes: Dict[str, UniversalNode] = {}
        self._graph: Optional[StateGraph] = None

    async def compile(self, checkpointer: Optional[Any] = None):
        """
        更具配置文件基于langgraph来编译工作流图(不限于工作流)
        功能：
            1、动态构建状态类(State),从而构建StateGraph类(langgraph框架需要)
                核心方法：self._create_state_class()
            2、更具配置文件构建节点、添加节点到图中以及编排节点之间的可达性
                核心方法:
                    await self._build_nodes()  构建节点
                    self._add_nodes_to_graph() 添加节点到图中
                    self._add_edges()  编排节点之间的可达性
                    self._graph.set_entry_point(self.config.entry_point) 设置入口节点
            3、配置记忆持久化模式
                目前默认内存模式
                # todo  后续追加自定义、mysql、Mongodb、redis等
        """
        # 1. 动态创建状态类
        state_class = self._create_state_class()

        # 2. 创建 StateGraph (状态图,还未被编译)
        self._graph = StateGraph(state_class)

        # 3. 构建节点
        await self._build_nodes()

        # 4. 添加节点到图
        self._add_nodes_to_graph()

        # 5. 添加边
        self._add_edges()

        # 6. 设置入口点
        self._graph.set_entry_point(self.config.entry_point)

        # 7. 编译并返回
        if checkpointer:
            return self._graph.compile(checkpointer=checkpointer)
        return self._graph.compile()

    def _create_state_class(self):
        """
        根据配置，动态生成State的类型定义
        功能: 根据配置文件的 state_schema 动态创建状态类(TypedDict 的字典结构)
        部分重要解释(operator.add VS add_messages)：
            TypedDict 定义字典结构
            Annotated 给类型附加额外元数据，在这端代码中，就是给自定义的State的类型添加而外元数据。Langgraph的框架就会根据附加的而外元数据进行处理。
                Annotated[python_type, add_messages],元数据可以是任何东西(包括自定义的处理方法)
                from langgraph.graph.message import add_messages 中  add_messages 就是 Langgraph 提供的一个元数据的方法。 LangGraph 用这个识别 reducer
                Langgraph的add_messages方法带有智能去重，专门用于信息流，非常适合现在llm模型的流式返回，核心原因是: 支持消息的修改和流式更新，而不仅仅是追加【重要】。
                比如在流式调用的过程中，AI 回复是逐步完成的，但是在没有完成前，id都是一样的，所以可以采用id去重：
                    # 第一个 chunk
                    add_messages(messages, [AIMessage(content="你好，", id="stream_1")])
                    # 第二个 chunk（替换，不是追加）
                    add_messages(messages, [AIMessage(content="你好，我是", id="stream_1")])
                    # 第三个 chunk
                    add_messages(messages, [AIMessage(content="你好，我是助手", id="stream_1")])
                再比如，工具调用后修改消息
                    messages = [
                        HumanMessage(content="北京天气怎么样？"),
                        AIMessage(content="", tool_calls=[{"name": "get_weather", "args": {"city": "北京"}}], id="ai_1")
                    ]
                    # 工具执行完成，需要把结果附加到同一条 AI 消息
                    # 如果用简单追加，会变成两条消息
                    # 用 add_messages + 相同 id，可以更新那条消息
                    new_messages = [
                        AIMessage(content="北京今天晴，25度", tool_calls=[...], id="ai_1")  # 同 id，替换
                    ]
                再比如: Human-in-the-loop 修改
                    # 用户想修改之前的提问
                    messages = [
                        HumanMessage(content="写一首诗", id="human_1"),
                        AIMessage(content="春眠不觉晓...", id="ai_1")
                    ]
                    # 用户编辑了自己的消息
                    add_messages(messages, [HumanMessage(content="写一首关于秋天的诗", id="human_1")])
                    # human_1 被替换，而不是追加一条新的
                    # 这样重新执行时，AI 会基于修改后的问题回答
                还有checkpoint 恢复后继续等
            operator.add: 是单纯的数据累加
                # 第一次写入
                analysis_results = []
                new_value = ["报告1"]
                analysis_results = operator.add(analysis_results, new_value)
                # 结果: ["报告1"]

                # 第二次写入（并行节点）
                new_value = ["报告2"]
                analysis_results = operator.add(analysis_results, new_value)
                # 结果: ["报告1", "报告2"]
        """
        from typing import TypedDict, Annotated
        from langgraph.graph.message import add_messages
        import operator

        annotations = {}  # 定义字典结构
        for field_name, field_config in self.config.state_schema.items():
            field_type = field_config.get("type", "str")
            reducer = field_config.get("reducer")

            python_type = self._resolve_type(field_type)

            if reducer == "add_messages":
                annotations[field_name] = Annotated[python_type, add_messages]
            elif reducer == "add":
                # 使用 operator.add 来累积列表
                annotations[field_name] = Annotated[python_type, operator.add]
            else:
                annotations[field_name] = python_type

        return TypedDict(f"{self.config.name}State", annotations)

    # noinspection PyMethodMayBeStatic
    def _resolve_type(self, type_str: str) -> type:
        """解析类型字符串"""
        type_map = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "List[str]": List[str],
            "Dict[str, Any]": Dict[str, Any],
        }
        return type_map.get(type_str, Any)

    async def _build_nodes(self):
        """
        构建配置文件中的节点，并将节点添加到 self._nodes 【字典结构，所以节点名称一定不能重复】
        核心功能： 根据配置文件中定义的节点，使用自定义的 UniversalNodeBuilder节点构建器来构建自定义的通用节点 UniversalNode，【目前只适配llm节点和code节点】
                 循环读取nodes内部的节点列表
        # todo  后续需要为及UniversalNode追加MCP功能，以便LLM节点能实现更加强大的功能
        """
        for node_cfg in self.config.nodes:
            node_name = node_cfg["name"]
            node_type = node_cfg["type"]

            builder = UniversalNodeBuilder(node_name)

            if node_type == "llm":
                llm_config = LLMConfig(**node_cfg.get("config", {}))
                builder.with_structure_output(llm_config)
            elif node_type == "code":
                code_config = CodeConfig(**node_cfg.get("config", {}))
                builder.with_custom_code_config(code_config)

            self._nodes[node_name] = await builder.build()

    def _add_nodes_to_graph(self):
        """
        根据配置文件中节点信息明确节点输入输出，并将节点添加到状态图(未被编译的图)【非常核心的一个方法】。
        核心功能：根据配置文件中节点信息将节点添加到图中，并根据input_mapping明确节点接收的信息和output_mapping明确结点输出的信息【input_mapping和output_mapping的信息来源必须与State状态类定义的一致】。
                node_fn方法对原始节点进行二次包装，映射输入输出。
        """
        for node_cfg in self.config.nodes:
            node_name = node_cfg["name"]
            node = self._nodes[node_name]
            node_type = node_cfg.get("type")
            input_mapping = node_cfg.get("input_mapping", {})
            output_mapping = node_cfg.get("output_mapping", {})
            async def node_fn(
                    state: dict,
                    n=node,
                    in_map=input_mapping,
                    out_map=output_mapping,
                    n_type=node_type
            ) -> dict:
                # 1. 提取输入
                input_data = self._extract_input(state, in_map)

                # 2. 执行节点，得到输出
                result = await n.run_node(input_data)

                # 3. 映射输出
                return self._map_output(result, out_map, node_type=n_type)

            self._graph.add_node(node_name, node_fn)

    # noinspection PyMethodMayBeStatic
    def _extract_input(self, state: dict, input_mapping: dict) -> Any:
        """
        根据配置文件中节点配置提取输入【重要部分】
        核心功能: 根据配置文件中节点的input_mapping提取输入，返回输入后，非常依赖UniversalNode节点对输入数据的处理
        """
        # 如果没有直接，直接返回state作为输入数据
        if not input_mapping:
            return state

        source = input_mapping.get("source")
        format_type = input_mapping.get("format", "raw")

        if not source:
            return state

        data = state.get(source, [])

        # 格式化处理
        if format_type == "chat_history":
            # 聊天历史转文本
            if isinstance(data, list):
                return "\n".join([
                    f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                    if isinstance(msg, dict)
                    else f"{getattr(msg, 'role', 'user')}: {getattr(msg, 'content', '')}"
                    for msg in data
                ])
            return str(data)

        elif format_type == "join":
            # 列表拼接
            separator = input_mapping.get("separator", "\n")
            if isinstance(data, list):
                return separator.join([str(item) for item in data])
            return str(data)

        elif format_type == "last":
            # 取最后一个
            if isinstance(data, list) and data:
                item = data[-1]
                if hasattr(item, "content"):
                    return item.content
                elif isinstance(item, dict):
                    return item.get("content", str(item))
                return str(item)
            return str(data)

        elif format_type == "raw":
            return data

        return data

    # noinspection PyMethodMayBeStatic
    def _map_output(self, result: Any, output_mapping: dict, node_type: str = None) -> dict:
        """
        根据配置映射输出
        核心功能: 根据配置文件中节点的output_mapping提取输入
        """
        has_messages = "messages" in self.config.state_schema
        output_dict = {}

        # 处理基础输出
        if not output_mapping:
            if isinstance(result, dict):
                output_dict = result.copy()
            else:
                output_dict = {"output": result}
        else:
            target = output_mapping.get("target")
            mode = output_mapping.get("mode", "replace")

            if not target:
                if isinstance(result, dict):
                    output_dict = result.copy()
                else:
                    output_dict = {"output": result}
            elif mode == "append":
                output_dict = {target: [result]}
            elif mode == "replace":
                output_dict = {target: result}
            elif mode == "message":
                content = result if isinstance(result, str) else str(result)
                output_dict = {"messages": [AIMessage(content=content)], target: result}
                return output_dict  # message 模式已经处理了 messages，直接返回
            else:
                output_dict = {target: result}

        # 如果 state_schema 有 messages 且是 LLM 节点，自动追加 AIMessage
        if has_messages and node_type == "llm" and "messages" not in output_dict:
            content = result if isinstance(result, str) else str(result)
            output_dict["messages"] = [AIMessage(content=content)]

        return output_dict

    def _add_edges(self):
        """
        編排节点之间边的关系
        核心功能：加载配置文件的edges上边的列表
            1、编排节点之间边的关系，目前边有两种类型，正常的边(normal)与条件边(conditional)
        """
        for edge_cfg in self.config.edges:
            edge_type = edge_cfg.get("type", "normal")

            if edge_type == "normal":
                source = edge_cfg["source"]
                target = edge_cfg["target"]
                if target == "END":
                    self._graph.add_edge(source, END)
                else:
                    self._graph.add_edge(source, target)

            elif edge_type == "conditional":
                source = edge_cfg["source"]
                condition_field = edge_cfg["condition_field"]
                condition_map = edge_cfg["condition_map"]
                default = edge_cfg.get("default", "END")

                # 处理 END 映射，包含所有可能的目标
                resolved_map = {}
                for k, v in condition_map.items():
                    resolved_map[k] = END if v == "END" else v

                # 确保 default 也在映射中
                default_target = END if default == "END" else default

                def make_router(condition_key: str, mapping: dict, default_val):
                    def router(state: dict) -> str:
                        value = state.get(condition_key)
                        return mapping.get(value, default_val)
                    return router

                # 收集所有可能的目标节点
                all_targets = list(set(resolved_map.values()) | {default_target})
                path_map = {t: t for t in all_targets}

                self._graph.add_conditional_edges(
                    source,
                    make_router(condition_field, resolved_map, default_target),
                    path_map
                )
