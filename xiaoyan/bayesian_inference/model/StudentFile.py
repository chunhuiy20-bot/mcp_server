from typing import Optional
from pydantic import BaseModel, Field


class StudentProfile(BaseModel):
    """
     用户需要提交的信息:
         gpa: 高中成绩单, 必须要提交
         a_level_or_ap: 英美两种学校体系，有则必须交。 A-Level：A*, A, B, C, D, E /  AP：5、4、3、2、1 。 分数传入模型要进行统一预处理
         sat_or_act:
            - 全球化的考试，虽然没有明确要求，但是从 2024 年开始，一些最顶尖的大学觉得“没有 SAT 实在没法公正选拔”，于是恢复了强制要求。名单（截至目前）：麻省理工(MIT)、耶鲁(Yale)、哈佛(Harvard)、达特茅斯(Dartmouth)、布朗(Brown)、加州理工(Caltech)、得州大学奥斯汀分校等。
            - sar: max_1600  min_1 。  act: max_36   min_1
         target_school：目标院校
    """
    gpa: float
    a_level_or_ap: Optional[float]
    sat_or_act: Optional[float]
    target_school: str



# 全人评估模型

# 硬指标

# 自主招生

class SchoolData(BaseModel):
    """
    需要拿到的目标学校信息(非用户提供)
        gpa_min_line: gpa成绩最低标准
    """
    gpa_min_line: float = Field(default=0.0, description="gpa成绩最低标准，默认为0")


