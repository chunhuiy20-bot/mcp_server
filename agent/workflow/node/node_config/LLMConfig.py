import os
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv
load_dotenv()


@dataclass
class LLMConfig:
    system_prompt: str
    model: str = field(default="gpt-4.1")
    temperature: float = field(default=0.0)
    mcp_list: list = field(default_factory=list)
    openai_api_key: str = field(default=os.getenv("OPENAI_API_KEY"))
    openai_api_base: str = field(default=os.getenv("OPENAI_API_BASE"))
    need_structure_output: bool = False  # 是否需要结构化输出
    output_schema: Optional[Dict[str, Any]] = None  # 如果需要结构化输出，必须配置输出模型的 JSON 配置
