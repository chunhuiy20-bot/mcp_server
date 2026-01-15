"""
# 动态 Pydantic 模型生成器（增强版）
# 功能: 用于根据 JSON 配置动态创建 Pydantic 模型
# 特性: 支持多轮解析、嵌套模型依赖解析、调试模式
# 场景: workflow中node的自由配置，用于 chat.completions.parse 生成结构化数据
"""
from pydantic import BaseModel, Field, create_model, ConfigDict
from typing import Any, Optional, List, Dict, Union, Type, Set
import json
import re


class DynamicModelFactory:
    """动态模型工厂类（增强版）"""

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
        """获取严格模式的基类"""
        if cls._strict_base is None:
            class StrictBase(BaseModel):
                model_config = ConfigDict(extra='forbid')

            cls._strict_base = StrictBase
        return cls._strict_base

    @classmethod
    def _extract_model_references(cls, type_str: str) -> Set[str]:
        """
        提取类型字符串中引用的模型名
        例如: "List[MbtiVO]" -> {"MbtiVO"}
              "Dict[str, CoreCompetencyVO]" -> {"CoreCompetencyVO"}
        """
        # 匹配所有 PascalCase 的模型名（通常以大写字母开头）
        matches = re.findall(r'\b([A-Z][a-zA-Z0-9]*(?:VO|Model)?)\b', type_str)

        # 过滤掉 Python 类型关键字
        keywords = {'List', 'Optional', 'Dict', 'Union', 'Any', 'Type', 'Set', 'Tuple'}
        return set(m for m in matches if m not in keywords)

    @classmethod
    def _can_create_model(cls, fields_config: Dict[str, Any], available_models: Set[str]) -> bool:
        """
        检查是否可以创建模型（所有依赖的模型都已存在）
        """
        for field_name, field_config in fields_config.items():
            if field_name.startswith("__"):
                continue

            type_str = field_config.get("type", "str")

            # 检查内联对象
            if type_str == "object" and "properties" in field_config:
                # 递归检查内联对象的字段
                if not cls._can_create_model(field_config["properties"], available_models):
                    return False
            elif type_str.startswith("List[object]") and "items" in field_config:
                # 递归检查 List[object] 的 items
                if not cls._can_create_model(field_config["items"], available_models):
                    return False
            else:
                # 提取引用的模型名
                referenced_models = cls._extract_model_references(type_str)
                # 检查所有引用的模型是否都已创建
                for ref_model in referenced_models:
                    if ref_model not in available_models:
                        return False

        return True

    @classmethod
    def _parse_type(cls, type_str: str, nested_models: Dict[str, Type[BaseModel]] = None) -> Type:
        """
        解析类型字符串
        优先级：嵌套模型 > 预定义复合类型 > 基础类型 > 动态解析
        """
        type_str = type_str.strip()

        # 优先检查嵌套模型引用（最高优先级）
        if nested_models and type_str in nested_models:
            return nested_models[type_str]

        # 预定义复合类型（如 List[str]）
        if type_str in cls.COMPLEX_TYPE_MAPPING:
            return cls.COMPLEX_TYPE_MAPPING[type_str]

        # 基础类型
        if type_str.lower() in cls.BASE_TYPE_MAPPING:
            return cls.BASE_TYPE_MAPPING[type_str.lower()]

        # Optional[X] - 支持嵌套模型
        optional_match = re.match(r'^Optional\[(.+)]$', type_str)
        if optional_match:
            inner_type = optional_match.group(1).strip()
            inner = cls._parse_type(inner_type, nested_models)
            return Optional[inner]

        # List[X] - 支持嵌套模型
        list_match = re.match(r'^List\[(.+)]$', type_str)
        if list_match:
            inner_type = list_match.group(1).strip()
            inner = cls._parse_type(inner_type, nested_models)
            return List[inner]

        # Dict[K, V] - 支持嵌套模型
        dict_match = re.match(r'^Dict\[(.+),\s*(.+)]$', type_str)
        if dict_match:
            key_type = dict_match.group(1).strip()
            value_type = dict_match.group(2).strip()
            key = cls._parse_type(key_type, nested_models)
            value = cls._parse_type(value_type, nested_models)
            return Dict[key, value]

        # Union[X, Y, ...] - 支持嵌套模型
        union_match = re.match(r'^Union\[(.+)]$', type_str)
        if union_match:
            types_str = union_match.group(1)
            types = [cls._parse_type(t.strip(), nested_models) for t in types_str.split(',')]
            return Union[tuple(types)]

        # 如果都不匹配，默认返回 str（并打印警告）
        print(f"警告: 未识别的类型 '{type_str}'，默认使用 str")
        return str

    @classmethod
    def _build_field(cls, field_config: Dict[str, Any], nested_models: Dict[str, Type[BaseModel]] = None) -> tuple:
        """
        核心功能: 处理配置文件中定义Pydantic模型的字段，转为元组
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
        for key in ["min_length", "max_length", "min_items", "max_items", "pattern", "ge", "le", "gt", "lt",
                    "multiple_of"]:
            if key in field_config:
                field_kwargs[key] = field_config[key]

        # 处理 required 和 default
        if required:
            field_kwargs["default"] = ...
        else:
            field_kwargs["default"] = default_value

        return field_type, Field(**field_kwargs)

    @classmethod
    def _create_inline_model(cls, properties: Dict[str, Any], nested_models: Dict[str, Type[BaseModel]] = None) -> Type[
        BaseModel]:
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
            strict_mode: bool = True,
            debug: bool = False,
            _nested_models: Dict[str, Type[BaseModel]] = None  # 内部参数：外部传入的嵌套模型
    ) -> Type[BaseModel]:
        """
        核心功能: 把工作流配置文件中output_schema需要的转为Pydantic 模型
        支持多轮解析，自动处理嵌套模型依赖关系
        """
        # 如果传入的是符合json的字符串形式，将其转为json
        if isinstance(config, str):
            config = json.loads(config)

        config = config.copy()

        # cache_key：模型名 + 配置哈希 作为缓存 key
        cache_key = f"{model_name}_{hash(json.dumps(config, sort_keys=True))}"
        if use_cache and cache_key in cls._model_cache:
            if debug:
                print(f"从缓存加载模型: {model_name}")
            return cls._model_cache[cache_key]

        # 添加Pydantic模型描述
        if model_doc is None:
            model_doc = config.pop("__doc__", None)

        # 处理 __nested__ 定义的嵌套模型
        nested_models: Dict[str, Type[BaseModel]] = _nested_models.copy() if _nested_models else {}
        nested_config = config.pop("__nested__", {})

        # 多轮解析：按依赖顺序创建嵌套模型
        if nested_config:
            if debug:
                print(f" 开始多轮解析嵌套模型 (共 {len(nested_config)} 个):")

            remaining = dict(nested_config)
            max_iterations = 20  # 防止死循环
            iteration = 0

            while remaining and iteration < max_iterations:
                iteration += 1
                created_in_this_round = []

                # 当前已创建的模型名集合
                available_models = set(nested_models.keys())

                for nested_name, nested_fields in list(remaining.items()):
                    # 检查这个模型的所有字段是否都能解析
                    if cls._can_create_model(nested_fields, available_models):
                        if debug:
                            print(f"  第 {iteration} 轮: 创建 {nested_name}")

                        # 创建模型
                        nested_models[nested_name] = cls.create(
                            nested_fields,
                            nested_name,
                            use_cache=False,
                            strict_mode=strict_mode,
                            debug=False,
                            _nested_models=nested_models  # 传递已创建的模型
                        )
                        created_in_this_round.append(nested_name)

                # 移除已创建的模型
                for name in created_in_this_round:
                    remaining.pop(name)

                # 如果这一轮没有创建任何模型，说明有循环依赖或配置错误
                if not created_in_this_round:
                    if remaining:
                        print(f"错误：无法解析以下模型（可能存在循环依赖或引用了不存在的模型）:")
                        for name, fields in remaining.items():
                            refs = set()
                            for field_name, field_config in fields.items():
                                if not field_name.startswith("__"):
                                    type_str = field_config.get("type", "str")
                                    refs.update(cls._extract_model_references(type_str))
                            missing = refs - set(nested_models.keys())
                            print(f"  - {name}: 缺少依赖 {missing}")
                    break

            if debug and nested_models:
                print(f"嵌套模型创建完成 (共 {len(nested_models)} 个):")
                for name in nested_models.keys():
                    print(f"  - {name}")

        # 构建字段（传入已创建的嵌套模型）
        fields = {}
        if debug:
            print(f"开始构建 {model_name} 的字段:")

        for field_name, field_config in config.items():
            if not field_name.startswith("__"):
                field_type, field_obj = cls._build_field(field_config, nested_models)
                fields[field_name] = (field_type, field_obj)

                if debug:
                    type_name = getattr(field_type, '__name__', str(field_type))
                    print(f"  - {field_name}: {type_name}")

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

        if debug:
            print(f"模型 {model_name} 创建成功")

        return model

    @classmethod
    def validate_schema(cls, model: Type[BaseModel], sample_data: Dict[str, Any] = None,
                        show_schema: bool = False) -> bool:
        """
        验证模型结构
        """
        try:
            schema = model.model_json_schema()
            print(f"模型 {model.__name__} 结构验证通过")
            for field_name, field_info in model.model_fields.items():
                print(f"  - {field_name}: {field_info.annotation}")

            if show_schema:
                print(f"完整 JSON Schema:")
                print(json.dumps(schema, indent=2, ensure_ascii=False))

            if sample_data:
                print(f"测试数据验证:")
                instance = model(**sample_data)
                print(f"数据验证通过")
                print(f"实例: {instance}")

            return True
        except Exception as e:
            print(f"模型验证失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    @classmethod
    def clear_cache(cls):
        """清空模型缓存"""
        cls._model_cache.clear()
        print("模型缓存已清空")


dynamic_model_factory = DynamicModelFactory()

# ==================== 使用示例 ====================
if __name__ == "__main__":
    print("=" * 60)
    print("测试 1: 基础嵌套模型")
    print("=" * 60)

    # 嵌套模型
    order_config = {
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

    OrderModel = DynamicModelFactory.create(order_config, "OrderModel", debug=True)

    sample_order = {
        "order_id": "ORD001",
        "address": {"city": "北京", "street": "朝阳区xxx路"},
        "products": [
            {"name": "笔记本", "price": 5999.0},
            {"name": "鼠标", "price": 199.0}
        ]
    }
    DynamicModelFactory.validate_schema(OrderModel, sample_order)

    print("\n" + "=" * 60)
    print("测试 2: 复杂嵌套依赖（多轮解析）")
    print("=" * 60)

    # 复杂嵌套：IdentityVO 依赖 MbtiVO 和 CoreCompetencyVO
    complex_config = {
        "__nested__": {
            "MbtiVO": {
                "code": {"type": "str", "description": "MBTI代码"},
                "label": {"type": "str", "description": "MBTI类型名称"}
            },
            "CoreCompetencyVO": {
                "id": {"type": "int"},
                "label": {"type": "str"}
            },
            "IdentityVO": {
                "mbti": {"type": "MbtiVO"},
                "core_competencies": {"type": "List[CoreCompetencyVO]"}
            }
        },
        "identity": {"type": "IdentityVO"}
    }

    ComplexModel = DynamicModelFactory.create(complex_config, "ComplexModel", debug=True)

    sample_complex = {
        "identity": {
            "mbti": {"code": "ENTJ", "label": "指挥官"},
            "core_competencies": [
                {"id": 1, "label": "战略规划"},
                {"id": 2, "label": "团队协作"}
            ]
        }
    }
    DynamicModelFactory.validate_schema(ComplexModel, sample_complex)
