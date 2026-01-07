"""
# 动态 Pydantic 模型生成器
# 功能: 用于根据 JSON 配置动态创建 Pydantic 模型
# 场景: workflow中node的自由配置，用于 chat.completions.parse 生成结构化数据，不再需要等方法调用完后解析json
"""
from pydantic import BaseModel, Field, create_model
from typing import Any, Optional, List, Dict, Union, Type
from enum import Enum
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
        "list": list,
        "array": list,
        "dict": dict,
        "object": dict,
        "any": Any,
    }

    # 复合类型映射
    COMPLEX_TYPE_MAPPING: Dict[str, Type] = {
        "List[str]": List[str],
        "List[int]": List[int],
        "List[float]": List[float],
        "List[bool]": List[bool],
        "List[Any]": List[Any],
        "Dict[str, str]": Dict[str, str],
        "Dict[str, int]": Dict[str, int],
        "Dict[str, Any]": Dict[str, Any],
        "Optional[str]": Optional[str],
        "Optional[int]": Optional[int],
        "Optional[float]": Optional[float],
        "Optional[bool]": Optional[bool],
        "Optional[list]": Optional[list],
        "Optional[dict]": Optional[dict],
    }

    # 缓存已创建的模型
    _model_cache: Dict[str, Type[BaseModel]] = {}

    @classmethod
    def _parse_type(cls, type_str: str, nested_models: Dict[str, Type[BaseModel]] = None) -> Type:
        """解析类型字符串"""
        type_str = type_str.strip()

        # 检查是否是嵌套模型引用
        if nested_models and type_str in nested_models:
            return nested_models[type_str]

        # 检查基础类型
        if type_str.lower() in cls.BASE_TYPE_MAPPING:
            return cls.BASE_TYPE_MAPPING[type_str.lower()]

        # 检查复合类型
        if type_str in cls.COMPLEX_TYPE_MAPPING:
            return cls.COMPLEX_TYPE_MAPPING[type_str]

        # 解析 Optional[NestedModel] 格式
        optional_match = re.match(r'^Optional\[(\w+)]$', type_str)
        if optional_match:
            inner_type = optional_match.group(1)
            inner = cls._parse_type(inner_type, nested_models)
            return Optional[inner]

        # 解析 List[NestedModel] 格式
        list_match = re.match(r'^List\[(\w+)]$', type_str)
        if list_match:
            inner_type = list_match.group(1)
            inner = cls._parse_type(inner_type, nested_models)
            return List[inner]

        # 默认返回 str
        return str

    @classmethod
    def _build_field(cls, field_config: Dict[str, Any], nested_models: Dict[str, Type[BaseModel]] = None) -> tuple:
        """构建字段定义"""
        # 获取类型
        type_str = field_config.get("type", "str")
        field_type = cls._parse_type(type_str, nested_models)

        # 获取基础配置
        description = field_config.get("description", "")
        required = field_config.get("required", True)
        default_value = field_config.get("default", None)
        title = field_config.get("title", None)
        examples = field_config.get("examples", None)

        # 构建 Field 参数
        field_kwargs: Dict[str, Any] = {}

        if description:
            field_kwargs["description"] = description
        if title:
            field_kwargs["title"] = title
        if examples:
            field_kwargs["examples"] = examples

        # 字符串验证规则
        if "min_length" in field_config:
            field_kwargs["min_length"] = field_config["min_length"]
        if "max_length" in field_config:
            field_kwargs["max_length"] = field_config["max_length"]
        if "pattern" in field_config:
            field_kwargs["pattern"] = field_config["pattern"]

        # 数值验证规则
        if "ge" in field_config:
            field_kwargs["ge"] = field_config["ge"]
        if "le" in field_config:
            field_kwargs["le"] = field_config["le"]
        if "gt" in field_config:
            field_kwargs["gt"] = field_config["gt"]
        if "lt" in field_config:
            field_kwargs["lt"] = field_config["lt"]
        if "multiple_of" in field_config:
            field_kwargs["multiple_of"] = field_config["multiple_of"]

        # 设置默认值
        if required:
            field_kwargs["default"] = ...
        else:
            field_kwargs["default"] = default_value

        return field_type, Field(**field_kwargs)

    @classmethod
    def create(
            cls,
            config: Union[str, Dict[str, Any]],
            model_name: str = "DynamicModel",
            model_doc: str = None,
            use_cache: bool = False
    ) -> Type[BaseModel]:
        """
        根据 JSON 配置创建 Pydantic 模型

        Args:
            config: JSON 字符串或字典配置
            model_name: 模型名称
            model_doc: 模型文档字符串
            use_cache: 是否使用缓存

        Returns:
            动态创建的 Pydantic 模型类

        配置格式:
        {
            "__doc__": "模型描述（可选）",
            "__nested__": {
                "NestedModelName": {
                    "field1": {"type": "str", "description": "字段1"}
                }
            },
            "field_name": {
                "type": "str|int|float|bool|list|dict|List[str]|Optional[int]|NestedModelName",
                "description": "字段描述",
                "required": true,
                "default": null,
                "title": "字段标题",
                "examples": ["示例值"],
                "min_length": 1,
                "max_length": 100,
                "pattern": "^[a-z]+$",
                "ge": 0,
                "le": 100,
                "gt": 0,
                "lt": 100,
                "multiple_of": 5
            }
        }
        """
        # 解析配置
        if isinstance(config, str):
            config = json.loads(config)

        # 检查缓存
        cache_key = f"{model_name}_{hash(json.dumps(config, sort_keys=True))}"
        if use_cache and cache_key in cls._model_cache:
            return cls._model_cache[cache_key]

        # 提取模型文档
        if model_doc is None:
            model_doc = config.pop("__doc__", None)

        # 处理嵌套模型
        nested_models: Dict[str, Type[BaseModel]] = {}
        nested_config = config.pop("__nested__", {})
        for nested_name, nested_fields in nested_config.items():
            nested_models[nested_name] = cls.create(
                nested_fields,
                nested_name,
                use_cache=False
            )

        # 构建字段
        fields = {}
        for field_name, field_config in config.items():
            if not field_name.startswith("__"):
                fields[field_name] = cls._build_field(field_config, nested_models)

        # 创建模型
        model = create_model(model_name, **fields)

        # 设置文档
        if model_doc:
            model.__doc__ = model_doc

        # 缓存模型
        if use_cache:
            cls._model_cache[cache_key] = model

        return model

    @classmethod
    def create_enum(cls, name: str, values: List[str]) -> Type[Enum]:
        """动态创建枚举类型"""
        return Enum(name, {v: v for v in values})

    @classmethod
    def clear_cache(cls):
        """清除模型缓存"""
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
    print(json.dumps(Output.model_json_schema(), indent=2, ensure_ascii=False))
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
    print()
