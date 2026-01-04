from typing import List
from pydantic import BaseModel, Field, ConfigDict



from enum import Enum


class StrengthKey(str, Enum):
    """
    盖洛普 34 才干枚举
    值必须严格对应前端字典的 Key (PascalCase)
    """
    # === 执行力 (Executing) ===
    ACHIEVER = "Achiever"
    ARRANGER = "Arranger"
    BELIEF = "Belief"
    CONSISTENCY = "Consistency"
    DELIBERATIVE = "Deliberative"
    DISCIPLINE = "Discipline"
    FOCUS = "Focus"
    RESPONSIBILITY = "Responsibility"
    RESTORATIVE = "Restorative"

    # === 影响力 (Influencing) ===
    ACTIVATOR = "Activator"
    COMMAND = "Command"
    COMMUNICATION = "Communication"
    COMPETITION = "Competition"
    MAXIMIZER = "Maximizer"
    SELF_ASSURANCE = "Self-Assurance"  # 注意中间的连字符
    SIGNIFICANCE = "Significance"
    WOO = "Woo"

    # === 关系建立 (Relationship Building) ===
    ADAPTABILITY = "Adaptability"
    CONNECTEDNESS = "Connectedness"
    DEVELOPER = "Developer"
    EMPATHY = "Empathy"
    HARMONY = "Harmony"
    INCLUDER = "Includer"
    INDIVIDUALIZATION = "Individualization"
    POSITIVITY = "Positivity"
    RELATOR = "Relator"

    # === 战略思维 (Strategic Thinking) ===
    ANALYTICAL = "Analytical"
    CONTEXT = "Context"
    FUTURISTIC = "Futuristic"
    IDEATION = "Ideation"
    INPUT = "Input"
    INTELLECTION = "Intellection"
    LEARNER = "Learner"
    STRATEGIC = "Strategic"


# --- 基础配置：自动转换驼峰命名 (camelCase -> snake_case) ---
class BaseVO(BaseModel):
    """
    所有 VO 的基类，配置了自动别名生成器。
    前端 JSON: studentName  <--> 后端 Python: student_name
    """
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda s: "".join([w.capitalize() if i > 0 else w for i, w in enumerate(s.split("_"))])
    )



# 2. Identity (MBTI & 核心能力)
class MbtiVO(BaseVO):
    code: str = Field(..., description="MBTI代码, 如 INTJ")
    label: str = Field(..., description="MBTI类型名称, 如 战略家")


class CoreCompetencyVO(BaseVO):
    id: int
    label: str = Field(..., description="能力标签, 如 情报分析师")


class IdentityVO(BaseVO):
    mbti: MbtiVO
    core_competencies: List[CoreCompetencyVO]


# 3. Personality (大五人格 & 详细分析)
class BigFiveScoresVO(BaseVO):
    openness: int = Field(..., ge=0, le=100)
    conscientiousness: int = Field(..., ge=0, le=100)
    extraversion: int = Field(..., ge=0, le=100)
    agreeableness: int = Field(..., ge=0, le=100)
    stability: int = Field(..., ge=0, le=100)

class PersonalityTag(BaseVO):
    label: str = Field(..., description="人格标签")
    color: str = Field(..., description="Hex 颜色值,e.g #ff0012")

class SummaryVO(BaseVO):
    title: str = Field(..., min_length=7,max_length=10, description="人格特质总结，eg. 安静且理性的探索者")
    tags: List[PersonalityTag] = Field(..., description="人格标签")
    description: str = Field(..., description="详细的文本分析")


class MetricVO(BaseVO):
    metric_type: int = Field(..., ge=1, le=2, description="1表示：心理能量与社交。2表示：行动策略与应变")
    list_value: List[int] = Field(..., min_length=2, max_length=2, description="当metric_type为1的时候，列表第一个表示内敛或观察，列表第二个表示深交或沉着特质。当metric_type为2的时候列表第一个表示计划或流程特质，第二个表示实干或经验特质。 数值0-100,越高越符合该特质")


class SubDimensionVO(BaseVO):
    metrics: List[MetricVO] = Field(..., min_length=2, max_length=2, description="子维度列表")


class PersonalityVO(BaseVO):
    big_five_scores: BigFiveScoresVO
    summary: SummaryVO
    sub_dimensions: List[SubDimensionVO]


# 4. CliftonStrengths (才干)
class StrengthSimpleVO(BaseModel):
    # 这里把类型从 str 改为 StrengthKey
    key: StrengthKey = Field(
        ...,
        description="才干英文Key（枚举），用于前端映射中文名和描述"
    )
    score: int = Field(..., description="测评得分")
    rank: int = Field(..., description="排名 1-34")



class TalentReportResponse(BaseVO):
    user_id: str
    identity: IdentityVO
    personality: PersonalityVO
    clifton_strengths: List[StrengthSimpleVO] = Field(..., min_length=34, max_length=34, description="34种才干列表")



# # 5. Application Pathways (应用路径表格)
# class PathwayThemeVO(BaseVO):
#     name: str = Field(..., description="才干中文名，如 '搜集'")
#     domain: str = Field(..., description="领域分类: exec, inf, rel, strat")
#
#
# class ApplicationPathwayVO(BaseVO):
#     themes: List[PathwayThemeVO] = Field(..., description="组合中的才干列表")
#     advice_title: str = Field(..., description="建议标题")
#     advice_content: str = Field(..., description="建议详细内容")


# --- 根响应模型 (Root Response) ---
# class TalentReportResponse(BaseVO):
#     meta: MetaVO
#     identity: IdentityVO
#     personality: PersonalityVO
#     clifton_strengths: List[StrengthSimpleVO]
    # application_pathways: List[ApplicationPathwayVO]