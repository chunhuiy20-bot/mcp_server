# ============ Python 代码执行器（无限制版本）============
import asyncio
from typing import Any

from agent.workflow.node.node_config.CodeConfig import CodeConfig
from agent.workflow.node.node_executor_strategy.NodeExecutor import NodeExecutor
import textwrap


class PythonCodeExecutor(NodeExecutor):
    """Python 代码执行器 - 无限制版本"""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    async def execute(self, input_data: Any, node_config: CodeConfig) -> Any:
        if not node_config.custom_code:
            raise ValueError("代码不能为空")

        # 去除代码的公共缩进（重要！）
        code = textwrap.dedent(node_config.custom_code)

        # 准备执行环境（完全开放）
        exec_namespace = {
            '__builtins__': __builtins__,
            'input_data': input_data,
            'result': None,
        }

        try:
            # 编译并执行
            compiled_code = compile(code, '<user_code>', 'exec')
            exec(compiled_code, exec_namespace, exec_namespace)

            # 如果定义了 process 函数，调用它
            if 'process' in exec_namespace:
                process_func = exec_namespace['process']
                if asyncio.iscoroutinefunction(process_func):
                    result = await asyncio.wait_for(
                        process_func(input_data),
                        timeout=self.timeout
                    )
                else:
                    result = process_func(input_data)
                return result

            # 否则返回 result 变量
            return exec_namespace.get('result')

        except asyncio.TimeoutError:
            raise TimeoutError(f"代码执行超时（{self.timeout}秒）")
        except Exception as e:
            raise RuntimeError(f"代码执行失败: {str(e)}")
