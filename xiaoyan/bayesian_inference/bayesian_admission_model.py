import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import warnings

warnings.filterwarnings('ignore')


@dataclass
class StudentProfile:
    """学生档案数据类 - 细粒度版本"""

    # 学术表现 (更细粒度)
    gpa: float  # 精确GPA值: 0.0-4.0
    sat_score: Optional[int] = None  # SAT分数: 400-1600
    act_score: Optional[int] = None  # ACT分数: 1-36
    ap_courses: int = 0  # AP课程数量
    ap_average_score: float = 0.0  # AP平均分: 1-5

    # 学术深度与求知欲
    research_papers: int = 0  # 发表论文数量
    research_projects: int = 0  # 参与科研项目数量
    academic_competitions_national: int = 0  # 国家级学术竞赛获奖
    academic_competitions_international: int = 0  # 国际级学术竞赛获奖
    independent_projects: int = 0  # 独立项目数量

    # 课外活动 (更细分)
    leadership_positions: int = 0  # 领导职位数量
    community_service_hours: int = 0  # 社区服务小时数
    sports_achievements: int = 0  # 体育成就 (0-5级)
    arts_achievements: int = 0  # 艺术成就 (0-5级)
    entrepreneurship: int = 0  # 创业经历 (0-3级)
    internships: int = 0  # 实习经历数量

    # 推荐信与文书质量
    recommendation_quality: int = 5  # 推荐信质量: 1-10
    essay_quality: int = 5  # 文书质量: 1-10

    # 背景
    school_tier: int = 3  # 学校层级: 1(顶尖)-5(普通)
    school_college_matriculation_rate: float = 0.5  # 学校历年名校录取率: 0-1
    legacy_status: bool = False  # 是否有校友关系
    first_generation: bool = False  # 是否第一代大学生
    underrepresented_minority: bool = False  # 是否少数族裔

    # 特殊才能
    special_talent: int = 0  # 特殊才能等级: 0-5 (如奥运选手、国际大奖等)

    def __post_init__(self):
        """数据验证"""
        if not 0 <= self.gpa <= 4.0:
            raise ValueError("GPA must be between 0.0 and 4.0")
        if self.sat_score and not 400 <= self.sat_score <= 1600:
            raise ValueError("SAT score must be between 400 and 1600")
        if self.act_score and not 1 <= self.act_score <= 36:
            raise ValueError("ACT score must be between 1 and 36")
        if not 0 <= self.ap_average_score <= 5:
            raise ValueError("AP average score must be between 0 and 5")
        if not 1 <= self.school_tier <= 5:
            raise ValueError("School tier must be between 1 and 5")
        if not 0 <= self.school_college_matriculation_rate <= 1:
            raise ValueError("Matriculation rate must be between 0 and 1")


class BayesianAdmissionModel:
    """
    细粒度贝叶斯大学录取概率模型

    核心改进:
    1. 多维度细粒度评估
    2. 非线性特征组合
    3. 动态权重调整
    4. 考虑特殊情况加成
    """

    def __init__(self, target_university_tier: str = 'top'):
        """
        初始化模型

        Args:
            target_university_tier: 目标大学层级
                - 'ivy_plus': 常春藤+斯坦福/MIT等 (录取率 3-6%)
                - 'top': Top 20 大学 (录取率 6-12%)
                - 'elite': Top 50 大学 (录取率 12-25%)
                - 'good': Top 100 大学 (录取率 25-50%)
        """
        self.target_tier = target_university_tier
        self.prior_admission = self._get_prior_admission()
        self._initialize_weights()

    def _get_prior_admission(self) -> float:
        """获取先验录取概率"""
        priors = {
            'ivy_plus': 0.045,  # 常春藤+ 约4.5%
            'top': 0.09,  # Top 20 约9%
            'elite': 0.18,  # Top 50 约18%
            'good': 0.35  # Top 100 约35%
        }
        return priors.get(self.target_tier, 0.10)

    def _initialize_weights(self):
        """初始化各维度权重（根据目标大学层级）"""
        if self.target_tier == 'ivy_plus':
            self.weights = {
                'academic_excellence': 0.35,  # 学术卓越
                'intellectual_curiosity': 0.25,  # 求知欲与学术深度
                'extracurricular_impact': 0.20,  # 课外活动影响力
                'personal_qualities': 0.12,  # 个人品质
                'background_context': 0.08  # 背景与多样性
            }
        elif self.target_tier == 'top':
            self.weights = {
                'academic_excellence': 0.40,
                'intellectual_curiosity': 0.22,
                'extracurricular_impact': 0.18,
                'personal_qualities': 0.12,
                'background_context': 0.08
            }
        elif self.target_tier == 'elite':
            self.weights = {
                'academic_excellence': 0.45,
                'intellectual_curiosity': 0.18,
                'extracurricular_impact': 0.17,
                'personal_qualities': 0.12,
                'background_context': 0.08
            }
        else:  # good
            self.weights = {
                'academic_excellence': 0.50,
                'intellectual_curiosity': 0.15,
                'extracurricular_impact': 0.15,
                'personal_qualities': 0.12,
                'background_context': 0.08
            }

    def _score_academic_excellence(self, student: StudentProfile) -> float:
        """
        评估学术卓越度 (0-100分)
        考虑: GPA, 标化考试, AP课程, 学校背景
        """
        score = 0.0

        # 1. GPA评分 (40分)
        # 根据学校层级调整GPA可信度 - 只能向下调整，不能向上
        school_trust_multiplier = {
            1: 1.0,  # 顶尖国际学校 - 不调整（最可信）
            2: 0.95,  # 知名国际学校 - 略微打折
            3: 0.88,  # 一般国际学校 - 打折
            4: 0.80,  # 普通国际学校 - 较大折扣
            5: 0.70  # 其他学校 - 大幅折扣
        }
        adjusted_gpa = student.gpa * school_trust_multiplier[student.school_tier]
        # 确保调整后的GPA不超过原始GPA
        adjusted_gpa = min(adjusted_gpa, student.gpa)

        if adjusted_gpa >= 3.95:
            gpa_score = 40
        elif adjusted_gpa >= 3.85:
            gpa_score = 35 + (adjusted_gpa - 3.85) * 50
        elif adjusted_gpa >= 3.7:
            gpa_score = 28 + (adjusted_gpa - 3.7) * 46.7
        elif adjusted_gpa >= 3.5:
            gpa_score = 18 + (adjusted_gpa - 3.5) * 50
        else:
            gpa_score = max(0, adjusted_gpa * 5)

        score += gpa_score

        # 2. 标化考试 (30分)
        test_score = 0
        if student.sat_score:
            if student.sat_score >= 1550:
                test_score = 30
            elif student.sat_score >= 1500:
                test_score = 25 + (student.sat_score - 1500) * 0.1
            elif student.sat_score >= 1450:
                test_score = 18 + (student.sat_score - 1450) * 0.14
            elif student.sat_score >= 1400:
                test_score = 10 + (student.sat_score - 1400) * 0.16
            else:
                test_score = max(0, (student.sat_score - 1200) * 0.05)
        elif student.act_score:
            if student.act_score >= 35:
                test_score = 30
            elif student.act_score >= 33:
                test_score = 25 + (student.act_score - 33) * 2.5
            elif student.act_score >= 30:
                test_score = 18 + (student.act_score - 30) * 2.33
            elif student.act_score >= 27:
                test_score = 10 + (student.act_score - 27) * 2.67
            else:
                test_score = max(0, (student.act_score - 20) * 1.43)

        score += test_score

        # 3. AP课程 (20分)
        ap_score = 0
        if student.ap_courses > 0:
            # AP数量分
            ap_count_score = min(student.ap_courses * 1.5, 10)
            # AP质量分
            if student.ap_average_score >= 4.5:
                ap_quality_score = 10
            elif student.ap_average_score >= 4.0:
                ap_quality_score = 7 + (student.ap_average_score - 4.0) * 6
            elif student.ap_average_score >= 3.5:
                ap_quality_score = 4 + (student.ap_average_score - 3.5) * 6
            else:
                ap_quality_score = max(0, student.ap_average_score)

            ap_score = ap_count_score + ap_quality_score

        score += ap_score

        # 4. 学校历史录取率加成 (10分)
        matriculation_bonus = student.school_college_matriculation_rate * 10
        score += matriculation_bonus

        return min(score, 100)

    def _score_intellectual_curiosity(self, student: StudentProfile) -> float:
        """
        评估求知欲与学术深度 (0-100分)
        考虑: 科研、竞赛、独立项目
        """
        score = 0.0

        # 1. 科研论文 (30分)
        if student.research_papers >= 3:
            paper_score = 30
        elif student.research_papers >= 2:
            paper_score = 25
        elif student.research_papers >= 1:
            paper_score = 18
        else:
            paper_score = 0
        score += paper_score

        # 2. 科研项目 (25分)
        project_score = min(student.research_projects * 8, 25)
        score += project_score

        # 3. 学术竞赛 (30分)
        competition_score = 0
        # 国际级竞赛权重更高
        competition_score += student.academic_competitions_international * 12
        competition_score += student.academic_competitions_national * 6
        competition_score = min(competition_score, 30)
        score += competition_score

        # 4. 独立项目 (15分)
        independent_score = min(student.independent_projects * 5, 15)
        score += independent_score

        return min(score, 100)

    def _score_extracurricular_impact(self, student: StudentProfile) -> float:
        """
        评估课外活动影响力 (0-100分)
        考虑: 领导力、社区服务、体育艺术、创业、实习
        """
        score = 0.0

        # 1. 领导力 (25分)
        if student.leadership_positions >= 3:
            leadership_score = 25
        elif student.leadership_positions >= 2:
            leadership_score = 20
        elif student.leadership_positions >= 1:
            leadership_score = 12
        else:
            leadership_score = 0
        score += leadership_score

        # 2. 社区服务 (20分)
        if student.community_service_hours >= 300:
            service_score = 20
        elif student.community_service_hours >= 200:
            service_score = 15
        elif student.community_service_hours >= 100:
            service_score = 10
        elif student.community_service_hours >= 50:
            service_score = 5
        else:
            service_score = student.community_service_hours * 0.05
        score += service_score

        # 3. 体育成就 (15分)
        sports_score = min(student.sports_achievements * 3, 15)
        score += sports_score

        # 4. 艺术成就 (15分)
        arts_score = min(student.arts_achievements * 3, 15)
        score += arts_score

        # 5. 创业经历 (15分)
        entrepreneurship_score = student.entrepreneurship * 5
        score += entrepreneurship_score

        # 6. 实习经历 (10分)
        internship_score = min(student.internships * 3.5, 10)
        score += internship_score

        return min(score, 100)

    def _score_personal_qualities(self, student: StudentProfile) -> float:
        """
        评估个人品质 (0-100分)
        考虑: 推荐信、文书质量
        """
        score = 0.0

        # 1. 推荐信质量 (50分)
        recommendation_score = (student.recommendation_quality / 10) * 50
        score += recommendation_score

        # 2. 文书质量 (50分)
        essay_score = (student.essay_quality / 10) * 50
        score += essay_score

        return score

    def _score_background_context(self, student: StudentProfile) -> float:
        """
        评估背景与多样性 (0-100分)
        考虑: 校友关系、第一代大学生、少数族裔、特殊才能
        """
        score = 50.0  # 基础分

        # 1. 校友关系 (Legacy) +20分
        if student.legacy_status:
            score += 20

        # 2. 第一代大学生 +15分
        if student.first_generation:
            score += 15

        # 3. 少数族裔 +10分
        if student.underrepresented_minority:
            score += 10

        # 4. 特殊才能 (最高+30分)
        if student.special_talent >= 5:  # 世界级
            score += 30
        elif student.special_talent >= 4:  # 国家级顶尖
            score += 25
        elif student.special_talent >= 3:  # 国家级
            score += 18
        elif student.special_talent >= 2:  # 省级顶尖
            score += 10
        elif student.special_talent >= 1:  # 省级
            score += 5

        return min(score, 100)

    def _calculate_competition_adjustment(self,
                                          student_scores: Dict[str, float],
                                          applicant_pool: List[StudentProfile]) -> Dict[str, float]:
        """
        计算竞争调整因子
        当申请池中高分学生扎堆时，调整评估策略
        """
        if not applicant_pool or len(applicant_pool) < 5:
            return {
                'academic_adjustment': 1.0,
                'other_adjustment': 1.0
            }

        # 计算申请池的学术卓越度分布
        pool_academic_scores = []
        for applicant in applicant_pool:
            pool_academic_scores.append(self._score_academic_excellence(applicant))

        avg_academic = np.mean(pool_academic_scores)
        student_academic = student_scores['academic_excellence']

        # 如果申请池平均学术分很高 (>85)，降低学术权重，提高其他维度权重
        if avg_academic >= 85:
            # 学生学术分高于平均，优势减弱
            if student_academic >= avg_academic:
                academic_adjustment = 0.7  # 学术优势打折
                other_adjustment = 1.3  # 其他维度加权
            else:
                academic_adjustment = 0.6
                other_adjustment = 1.2
        elif avg_academic >= 75:
            academic_adjustment = 0.85
            other_adjustment = 1.15
        else:
            academic_adjustment = 1.0
            other_adjustment = 1.0

        return {
            'academic_adjustment': academic_adjustment,
            'other_adjustment': other_adjustment
        }

    def calculate_admission_probability(self,
                                        student: StudentProfile,
                                        applicant_pool: List[StudentProfile] = None,
                                        verbose: bool = False) -> Dict:
        """
        计算学生的录取概率

        Args:
            student: 学生档案
            applicant_pool: 申请者池（用于竞争调整）
            verbose: 是否输出详细信息

        Returns:
            包含录取概率和详细分析的字典
        """
        # 1. 计算各维度得分
        scores = {
            'academic_excellence': self._score_academic_excellence(student),
            'intellectual_curiosity': self._score_intellectual_curiosity(student),
            'extracurricular_impact': self._score_extracurricular_impact(student),
            'personal_qualities': self._score_personal_qualities(student),
            'background_context': self._score_background_context(student)
        }

        # 2. 竞争调整
        if applicant_pool is None:
            applicant_pool = [student]

        competition_adj = self._calculate_competition_adjustment(scores, applicant_pool)

        # 3. 应用权重和竞争调整
        weighted_score = 0.0
        adjusted_weights = self.weights.copy()

        # 调整学术权重
        adjusted_weights['academic_excellence'] *= competition_adj['academic_adjustment']

        # 调整其他维度权重
        for key in ['intellectual_curiosity', 'extracurricular_impact', 'personal_qualities', 'background_context']:
            adjusted_weights[key] *= competition_adj['other_adjustment']

        # 重新归一化权重
        total_weight = sum(adjusted_weights.values())
        for key in adjusted_weights:
            adjusted_weights[key] /= total_weight

        # 计算加权分数
        for dimension, score in scores.items():
            weighted_score += scores[dimension] * adjusted_weights[dimension]

        # 4. 转换为概率
        # 使用Sigmoid函数将分数映射到概率
        # 调整参数使得分数与录取率匹配
        if self.target_tier == 'ivy_plus':
            # 更严格的标准
            z = (weighted_score - 85) / 8
        elif self.target_tier == 'top':
            z = (weighted_score - 80) / 10
        elif self.target_tier == 'elite':
            z = (weighted_score - 75) / 12
        else:  # good
            z = (weighted_score - 70) / 15

        base_probability = 1 / (1 + np.exp(-z))

        # 5. 结合先验概率（贝叶斯调整）
        # P(录取|特征) ∝ P(特征|录取) * P(录取)
        likelihood_ratio = base_probability / (1 - base_probability + 1e-10)
        prior_odds = self.prior_admission / (1 - self.prior_admission)
        posterior_odds = likelihood_ratio * prior_odds
        final_probability = posterior_odds / (1 + posterior_odds)

        # 6. 特殊情况加成
        if student.special_talent >= 5:
            final_probability = min(final_probability * 1.5, 0.95)
        elif student.special_talent >= 4:
            final_probability = min(final_probability * 1.3, 0.90)

        # 学校信誉调整系数（只能向下调整）
        school_trust_multiplier = {1: 1.0, 2: 0.95, 3: 0.88, 4: 0.80, 5: 0.70}
        adjusted_gpa = min(student.gpa * school_trust_multiplier[student.school_tier], student.gpa)

        # 构建结果
        result = {
            'admission_probability': final_probability,
            'weighted_score': weighted_score,
            'dimension_scores': scores,
            'adjusted_weights': adjusted_weights,
            'competition_adjustment': competition_adj,
            'base_probability': base_probability,
            'prior_admission': self.prior_admission,
            'school_trust_multiplier': school_trust_multiplier[student.school_tier],
            'adjusted_gpa': adjusted_gpa
        }

        if verbose:
            self._print_detailed_analysis(student, result)

        return result

    def _print_detailed_analysis(self, student: StudentProfile, result: Dict):
        """打印详细分析"""
        print("\n" + "=" * 80)
        print(f"录取概率详细分析 - {self.target_tier.upper()} 层级大学")
        print("=" * 80)

        print(f"\n【学术表现】")
        print(f"  GPA: {student.gpa:.2f} (学校层级{student.school_tier}) → 调整后: {result['adjusted_gpa']:.2f}")
        if student.sat_score:
            print(f"  SAT: {student.sat_score}")
        if student.act_score:
            print(f"  ACT: {student.act_score}")
        print(f"  AP课程: {student.ap_courses}门, 平均分: {student.ap_average_score:.1f}")

        print(f"\n【学术深度】")
        print(f"  研究论文: {student.research_papers}篇")
        print(f"  科研项目: {student.research_projects}个")
        print(
            f"  学术竞赛: 国际{student.academic_competitions_international}项, 国家{student.academic_competitions_national}项")
        print(f"  独立项目: {student.independent_projects}个")

        print(f"\n【课外活动】")
        print(f"  领导职位: {student.leadership_positions}个")
        print(f"  社区服务: {student.community_service_hours}小时")
        print(f"  体育成就: {student.sports_achievements}级, 艺术成就: {student.arts_achievements}级")
        print(f"  创业经历: {student.entrepreneurship}级, 实习: {student.internships}次")

        print(f"\n【个人品质】")
        print(f"  推荐信质量: {student.recommendation_quality}/10")
        print(f"  文书质量: {student.essay_quality}/10")

        print(f"\n【背景】")
        print(f"  学校名校录取率: {student.school_college_matriculation_rate:.1%}")
        print(f"  校友关系: {'是' if student.legacy_status else '否'}")
        print(f"  第一代大学生: {'是' if student.first_generation else '否'}")
        print(f"  少数族裔: {'是' if student.underrepresented_minority else '否'}")
        print(f"  特殊才能: {student.special_talent}级")

        print(f"\n【维度评分】(满分100)")
        for dim, score in result['dimension_scores'].items():
            weight = result['adjusted_weights'][dim]
            print(f"  {dim:30s}: {score:5.1f}分 (权重: {weight:.1%})")

        print(f"\n【综合评估】")
        print(f"  加权总分: {result['weighted_score']:.1f}/100")
        print(f"  竞争调整: 学术×{result['competition_adjustment']['academic_adjustment']:.2f}, "
              f"其他×{result['competition_adjustment']['other_adjustment']:.2f}")
        print(f"  基础概率: {result['base_probability']:.2%}")
        print(f"  先验概率: {result['prior_admission']:.2%}")

        print(f"\n【最终结果】")
        print(f"  录取概率: {result['admission_probability']:.2%}")

        # 给出建议
        if result['admission_probability'] >= 0.5:
            level = "很高"
        elif result['admission_probability'] >= 0.3:
            level = "较高"
        elif result['admission_probability'] >= 0.15:
            level = "中等"
        elif result['admission_probability'] >= 0.05:
            level = "较低"
        else:
            level = "很低"
        print(f"  评估等级: {level}")

        print("=" * 80 + "\n")

    def compare_students(self, students: List[Tuple[str, StudentProfile]],
                         applicant_pool: List[StudentProfile] = None) -> pd.DataFrame:
        """比较多个学生的录取概率"""
        if applicant_pool is None:
            applicant_pool = [s[1] for s in students]

        results = []
        for name, student in students:
            result = self.calculate_admission_probability(student, applicant_pool)
            results.append({
                '学生': name,
                'GPA': f"{student.gpa:.2f}",
                '标化': student.sat_score or student.act_score or 'N/A',
                'AP': student.ap_courses,
                '科研': student.research_papers + student.research_projects,
                '竞赛': student.academic_competitions_international + student.academic_competitions_national,
                '综合分': f"{result['weighted_score']:.1f}",
                '录取概率': f"{result['admission_probability']:.2%}",
                '录取概率值': result['admission_probability']
            })

        df = pd.DataFrame(results)
        df = df.sort_values('录取概率值', ascending=False).reset_index(drop=True)
        return df.drop('录取概率值', axis=1)