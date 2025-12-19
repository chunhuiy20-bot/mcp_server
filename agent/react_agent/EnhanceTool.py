from langchain_core.tools import BaseTool
from typing import Any
from pydantic import Field


class EnhanceTool(BaseTool):
    """用户上下文工具包装器，继承自BaseTool"""

    # 声明额外的字段
    original_tool: Any = Field(description="原始工具对象")
    user_id: str = Field(description="用户ID")
    needs_user_id: bool = Field(default=False, description="是否需要user_id参数")

    def __init__(self, original_tool, user_id: str, **kwargs):
        # 检查是否需要user_id
        needs_user_id = self._check_has_user_id_param_static(original_tool)

        # 调用父类初始化
        super().__init__(
            name=original_tool.name,
            description=original_tool.description,
            original_tool=original_tool,
            user_id=user_id,
            needs_user_id=needs_user_id,
            return_direct=getattr(original_tool, 'return_direct', False),
            verbose=getattr(original_tool, 'verbose', False),
            **kwargs
        )

        # 复制其他属性
        self._copy_tool_attributes()

    @staticmethod
    def _check_has_user_id_param_static(original_tool) -> bool:
        """静态方法检查工具参数定义中是否包含user_id"""
        try:
            if hasattr(original_tool, 'args_schema') and original_tool.args_schema:
                schema = original_tool.args_schema

                if isinstance(schema, dict) and 'properties' in schema:
                    properties = schema['properties']
                    fields = list(properties.keys())
                    has_user_id = 'user_id' in fields
                    # print(f" [参数检查] {original_tool.name} - 参数: {fields}, 有user_id: {has_user_id}")
                    return has_user_id
                else:
                    # print(f" [参数检查] {original_tool.name} - schema格式不符合预期")
                    return False
            else:
                # print(f" [参数检查] {original_tool.name} - 没有找到args_schema")
                return False

        except Exception as e:
            print(f" [参数检查] {original_tool.name} - 检查参数时出错: {e}")
            return False

    def _copy_tool_attributes(self):
        """复制原始工具的属性"""
        safe_attrs = [
            'args_schema', 'callbacks', 'tags', 'metadata',
            'handle_tool_error', 'handle_validation_error'
        ]

        for attr in safe_attrs:
            if hasattr(self.original_tool, attr):
                value = getattr(self.original_tool, attr)
                setattr(self, attr, value)

        # 特殊处理 args_schema，移除 user_id 参数
        if hasattr(self.original_tool, 'args_schema') and self.original_tool.args_schema:
            original_schema = self.original_tool.args_schema
            if isinstance(original_schema, dict) and 'properties' in original_schema:
                # 复制schema并移除user_id
                modified_schema = original_schema.copy()
                modified_properties = modified_schema['properties'].copy()

                # 如果有user_id参数，就移除它
                if 'user_id' in modified_properties:
                    del modified_properties['user_id']
                    modified_schema['properties'] = modified_properties

                    # 同时从required字段中移除user_id（如果存在）
                    if 'required' in modified_schema and isinstance(modified_schema['required'], list):
                        modified_required = [req for req in modified_schema['required'] if req != 'user_id']
                        modified_schema['required'] = modified_required

                    print(f"🔧 [Schema修改] 从工具 {self.name} 的schema中移除了user_id参数")

                setattr(self, 'args_schema', modified_schema)
            else:
                # 如果schema格式不符合预期，直接复制
                setattr(self, 'args_schema', original_schema)

    def _run(self, *args, **kwargs) -> Any:
        """同步运行方法（BaseTool要求实现）"""
        raise NotImplementedError("请使用 _arun 方法进行异步调用")

    async def _arun(self, *args, **kwargs) -> Any:
        """异步运行方法（BaseTool要求实现）"""
        print("=========================================================================")
        print(f"[工具 {self.name} 被调用], 参数: {args}， kwargs={kwargs}")
        # 处理参数
        if args and not kwargs:
            input_dict = {}
        else:
            input_dict = kwargs.copy()

        # 只有参数定义中包含user_id才注入
        if self.needs_user_id:
            input_dict["user_id"] = self.user_id
            print(f"🔧 [工具调用] 注入user_id: {self.user_id}")
        else:
            print(f"🔧 [工具调用] 直接使用原始参数")


        # 调用原始工具
        return await self.original_tool.ainvoke(input_dict)

    async def ainvoke(self, input_dict, config=None, **kwargs):
        """异步调用方法（LangChain标准接口）"""
        print(f"[工具 {self.name} 被调用], 入参: {input_dict}")

        # 处理输入参数
        if isinstance(input_dict, dict):
            processed_input = input_dict.copy()
        else:
            # 如果输入不是字典，尝试转换
            processed_input = {}

        # 只有参数定义中包含user_id才注入
        if self.needs_user_id:
            # 检查是否有args字段（LangChain工具调用格式）
            if 'args' in processed_input and isinstance(processed_input['args'], dict):
                # 修改args内的user_id
                processed_input['args']['user_id'] = self.user_id
                print(f"[工具调用] 在args中注入user_id: {self.user_id}")
        else:
            print(f"[工具调用] 直接使用原始参数")

        # 调用原始工具，传递config参数
        try:
            if config is not None:
                # 如果原始工具支持config参数
                print(f"[工具调用] 使用config参数：{processed_input}， config参数: {config}")
                return await self.original_tool.ainvoke(processed_input, config)
            else:
                print(f"[工具调用] 不使用config参数：{processed_input}")
                return await self.original_tool.ainvoke(processed_input)
        except TypeError as e:
            # 如果原始工具不支持config参数，只传递input
            if "takes" in str(e) and "positional arguments" in str(e):
                return await self.original_tool.ainvoke(processed_input)
            else:
                raise e

    async def invoke(self, input_dict, config=None, **kwargs):
        """同步调用方法的异步版本"""
        return await self.ainvoke(input_dict, config, **kwargs)
