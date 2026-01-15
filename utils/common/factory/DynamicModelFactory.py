"""
# 动态 Pydantic 模型生成器
# 功能: 用于根据 JSON 配置动态创建 Pydantic 模型
# 场景: workflow中node的自由配置，用于 chat.completions.parse 生成结构化数据，不再需要等方法调用完后解析json
"""
from pydantic import BaseModel, Field, create_model, ConfigDict
from typing import Any, Optional, List, Dict, Union, Type
import json
import re


class DynamicModelFactory:
    """动态模型工厂类"""

    # 基础类型映射
    BASE_TYPE_MAPPING: Dict[str, Type] = {
        "str": str,
        "string": str,
        "int": int,
        "integer": int,
        "float": float,
        "number": float,
        "bool": bool,
        "boolean": bool,
        "any": Any,
    }

    # 复杂类型映射
    COMPLEX_TYPE_MAPPING: Dict[str, Type] = {
        "List[str]": List[str],
        "List[int]": List[int],
        "List[float]": List[float],
        "List[bool]": List[bool],
        "Optional[str]": Optional[str],
        "Optional[int]": Optional[int],
        "Optional[float]": Optional[float],
        "Optional[bool]": Optional[bool],
    }

    _model_cache: Dict[str, Type[BaseModel]] = {}
    _strict_base: Type[BaseModel] = None

    @classmethod
    def _get_strict_base(cls) -> Type[BaseModel]:
        if cls._strict_base is None:
            class StrictBase(BaseModel):
                model_config = ConfigDict(extra='forbid')

            cls._strict_base = StrictBase
        return cls._strict_base

    @classmethod
    def _parse_type(cls, type_str: str, nested_models: Dict[str, Type[BaseModel]] = None) -> Type:
        """解析类型字符串"""
        type_str = type_str.strip()

        # 检查嵌套模型引用
        if nested_models and type_str in nested_models:
            return nested_models[type_str]

        # 基础类型
        if type_str.lower() in cls.BASE_TYPE_MAPPING:
            return cls.BASE_TYPE_MAPPING[type_str.lower()]

        # 预定义复合类型
        if type_str in cls.COMPLEX_TYPE_MAPPING:
            return cls.COMPLEX_TYPE_MAPPING[type_str]

        # Optional[X]
        optional_match = re.match(r'^Optional\[(\w+)]$', type_str)
        if optional_match:
            inner_type = optional_match.group(1)
            inner = cls._parse_type(inner_type, nested_models)
            return Optional[inner]

        # List[X]
        list_match = re.match(r'^List\[(\w+)]$', type_str)
        if list_match:
            inner_type = list_match.group(1)
            inner = cls._parse_type(inner_type, nested_models)
            return List[inner]

        return str

    @classmethod
    def _build_field(cls, field_config: Dict[str, Any], nested_models: Dict[str, Type[BaseModel]] = None) -> tuple:
        """
        核心功能: 处理配置文件中定义Pydantic模型的字段，转为元祖
            1、核心点：动态创建Pydantic模型
                create_model 方法是Pydantic 包提供的一个动态创建Pydantic模型的方法
                例如:
                class User(BaseModel):
                    name: str = Field(description="用户名")
                    age: int = Field(default=0, ge=0)
                等价于
                User = create_model(
                    "User",
                    name=(str, Field(description="用户名")),      # 元组：(类型, Field)
                    age=(int, Field(default=0, ge=0))              # 元组：(类型, Field)
                )
            2、核心点：处理内联情况兼容 (即在类内定义类，一般不推荐，结构不够清晰)
            {
              "user": {
                "type": "object",
                "properties": {
                  "name": {"type": "str"},
                  "age": {"type": "int"}
                }
              }
            }

        field_config: 单个字段的配置
        nested_models: 已创建的嵌套模型字典
        如: field_config:{'type': 'List[Product]', 'description': '商品列表', 'required': True} nested_models:{'Address': <class '__main__.Address'>, 'Product': <class '__main__.Product'>}
        """

        type_str = field_config.get("type", "str")

        # 检查是否是内联对象定义
        if type_str == "object" and "properties" in field_config:
            # 内联对象，动态创建嵌套模型
            inline_model = cls._create_inline_model(field_config["properties"], nested_models)
            field_type = inline_model
        elif type_str.startswith("List[object]") and "items" in field_config:
            # List[object] 带 items 定义
            item_model = cls._create_inline_model(field_config["items"], nested_models)
            field_type = List[item_model]
        else:
            field_type = cls._parse_type(type_str, nested_models)

        description = field_config.get("description", "")
        required = field_config.get("required", True)
        default_value = field_config.get("default", None)

        field_kwargs: Dict[str, Any] = {}
        if description:
            field_kwargs["description"] = description

        # 验证规则
        for key in ["min_length", "max_length", "pattern", "ge", "le", "gt", "lt", "multiple_of"]:
            if key in field_config:
                field_kwargs[key] = field_config[key]

        if required:
            field_kwargs["default"] = ...
        else:
            field_kwargs["default"] = default_value

        return field_type, Field(**field_kwargs)

    @classmethod
    def _create_inline_model(cls, properties: Dict[str, Any], nested_models: Dict[str, Type[BaseModel]] = None) -> Type[BaseModel]:
        """创建内联对象模型（严格模式）"""
        fields = {}
        for field_name, field_config in properties.items():
            fields[field_name] = cls._build_field(field_config, nested_models)

        # 生成唯一名称
        import hashlib
        name_hash = hashlib.md5(json.dumps(properties, sort_keys=True).encode()).hexdigest()[:8]
        model_name = f"InlineModel_{name_hash}"

        return create_model(
            model_name,
            __base__=cls._get_strict_base(),
            **fields
        )

    @classmethod
    def create(
            cls,
            config: Union[str, Dict[str, Any]],
            model_name: str = "DynamicModel",
            model_doc: str = None,
            use_cache: bool = False,
            strict_mode: bool = True
    ) -> Type[BaseModel]:
        """
        核心功能: 把工作流配置文件中output_schema需要的转为Pydantic 模型。OpenAI 的 chat.completions.parse 需要传入一个 Pydantic 模型来定义输出结构。但是这个方法不仅可以用于这里，可以用于其他地方
        :param config:  配置文件中的output_schema
        :param model_name: Pydantic 模型名称
        :param model_doc: Pydantic 模型介绍
        :param use_cache: 是否缓存这个模型
        :param strict_mode: 是否允许额外字段【LLM模型需要的是严格模式】
        :return: 返回 Pydantic 模型
        """
        # 如果传入的是符合json的字符串形式，将其转为json
        if isinstance(config, str):
            config = json.loads(config)


        config = config.copy()
        # cache_key：模型名 + 配置哈希 作为缓存 key,避免重复加载,相同配置不重复创建模型，提升性能
        cache_key = f"{model_name}_{hash(json.dumps(config, sort_keys=True))}"
        if use_cache and cache_key in cls._model_cache:
            return cls._model_cache[cache_key]

        # 添加Pydantic模型描述
        if model_doc is None:
            model_doc = config.pop("__doc__", None)

        # 处理 __nested__ 定义的嵌套模型
        nested_models: Dict[str, Type[BaseModel]] = {}
        nested_config = config.pop("__nested__", {})

        # 递归处理嵌套字段
        for nested_name, nested_fields in nested_config.items():
            nested_models[nested_name] = cls.create(
                nested_fields,
                nested_name,
                use_cache=False,
                strict_mode=strict_mode
            )

        # 构建字段
        fields = {}
        for field_name, field_config in config.items():
            if not field_name.startswith("__"):
                fields[field_name] = cls._build_field(field_config, nested_models)

        # 创建模型
        if strict_mode:
            model = create_model(
                model_name,
                __base__=cls._get_strict_base(),
                **fields
            )
        else:
            model = create_model(model_name, **fields)

        if model_doc:
            model.__doc__ = model_doc

        if use_cache:
            cls._model_cache[cache_key] = model
        print(f"pydantic model:{model}")
        return model

    @classmethod
    def clear_cache(cls):
        cls._model_cache.clear()


dynamic_model_factory = DynamicModelFactory()


# ==================== 使用示例 ====================
if __name__ == "__main__":

    # 嵌套模型
    user_config = {
        "__doc__": "订单模型",
        "__nested__": {
            "Address": {
                "city": {"type": "str", "description": "城市"},
                "street": {"type": "str", "description": "街道"},
                "zip_code": {"type": "Optional[str]", "description": "邮编", "required": False}
            },
            "Product": {
                "name": {"type": "str", "description": "商品名"},
                "price": {"type": "float", "description": "价格", "ge": 0}
            }
        },
        "order_id": {
            "type": "str",
            "description": "订单ID",
            "required": True
        },
        "address": {
            "type": "Address",
            "description": "收货地址",
            "required": True
        },
        "products": {
            "type": "List[Product]",
            "description": "商品列表",
            "required": True
        }
    }

    Output = DynamicModelFactory.create(user_config, "OutputModel", "订单模型")
    # print(json.dumps(Output.model_json_schema(), indent=2, ensure_ascii=False))
    order = Output(
        order_id="ORD001",
        address={"city": "北京", "street": "朝阳区xxx路"},
        products=[
            {"name": "笔记本", "price": 5999.0},
            {"name": "鼠标", "price": 199.0}
        ]
    )
    print(order)

    basic_config = {
        "__doc__": "用户信息模型",
        "name": {
            "type": "str",
            "description": "用户名称"
        },
        "age": {
            "type": "int",
            "description": "年龄"

        },
        "email": {
            "type": "Optional[str]",
            "description": "邮箱地址"
        },
        "tags": {
            "type": "List[str]",
            "description": "标签列表",
            "default": [],
            "required": False
        }
    }

    UserModel = DynamicModelFactory.create(basic_config, "UserModel")
    user = UserModel(name="张三", age=25, email="zhangsan@example.com")
    print("基础示例:")
    print(user)
