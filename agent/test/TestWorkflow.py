from time import sleep

from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator


# 定义状态结构 - 使用 Annotated 处理并发更新
class GraphState(TypedDict):
    input: str
    results: Annotated[list, operator.add]  # 使用 list 累积结果
    final_result: str


# 定义各个节点的处理函数
def start_node(state: GraphState) -> GraphState:
    """起始节点"""
    print(f"Start: 处理输入 - {state['input']}")
    return {"results": []}  # 初始化结果列表


def node_a(state: GraphState) -> GraphState:
    """节点 A"""
    sleep(30)
    print("节点 A: 处理中...")

    return {"results": [f"A处理了: {state['input']}"]}


def node_b(state: GraphState) -> GraphState:
    """节点 B"""
    sleep(10)
    print("节点 B: 处理中...")

    return {"results": [f"B处理了: {state['input']}"]}


def node_c(state: GraphState) -> GraphState:
    """节点 C"""
    sleep(1)
    print("节点 C: 处理中...")
    return {"results": [f"C处理了: {state['input']}"]}


def node_f(state: GraphState) -> GraphState:
    """节点 F - 汇总所有结果"""
    print("节点 F: 汇总结果...")
    all_results = ", ".join(state['results'])
    return {"final_result": f"最终结果: {all_results}"}


# 构建图
workflow = StateGraph(GraphState)

# 添加节点
workflow.add_node("start", start_node)
workflow.add_node("a", node_a)
workflow.add_node("b", node_b)
workflow.add_node("c", node_c)
workflow.add_node("f", node_f)

# 设置入口点
workflow.set_entry_point("start")

# 从 start 并行分发到 A、B、C
workflow.add_edge("start", "a")
workflow.add_edge("start", "b")
workflow.add_edge("start", "c")

# A、B、C 都流向 F
workflow.add_edge("a", "f")
workflow.add_edge("b", "f")
workflow.add_edge("c", "f")

# F 节点完成后结束
workflow.add_edge("f", END)

# 编译图
app = workflow.compile()

# 运行示例
if __name__ == "__main__":
    initial_state = {
        "input": "测试数据",
        "results": [],
        "final_result": ""
    }

    result = app.invoke(initial_state)
    print("\n=== 执行结果 ===")
    print(f"最终输出: {result['final_result']}")
    print(f"所有结果: {result['results']}")
