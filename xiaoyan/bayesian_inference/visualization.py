import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from typing import List, Tuple
from bayesian_admission_model import BayesianAdmissionModel, StudentProfile

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


class AdmissionVisualizer:
    """录取概率可视化工具"""

    def __init__(self, model: BayesianAdmissionModel):
        self.model = model

    def plot_sensitivity_analysis(self, base_student: StudentProfile,
                                  applicant_pool: List[StudentProfile] = None,
                                  figsize=(15, 10)):
        """
        绘制所有特征的敏感性分析图
        """
        features = ['gpa', 'curiosity', 'activity', 'school']
        feature_names = {
            'gpa': 'GPA等级',
            'curiosity': '求知欲',
            'activity': '课外活动',
            'school': '学校信誉'
        }

        fig, axes = plt.subplots(2, 2, figsize=figsize)
        axes = axes.flatten()

        for idx, feature in enumerate(features):
            df = self.model.sensitivity_analysis(base_student, feature, applicant_pool)

            ax = axes[idx]
            bars = ax.bar(df['特征值'], df['录取概率'], color='steelblue', alpha=0.7)

            # 添加数值标签
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2., height,
                        f'{height:.1%}',
                        ha='center', va='bottom', fontsize=10)

            ax.set_xlabel(feature_names[feature], fontsize=12, fontweight='bold')
            ax.set_ylabel('录取概率', fontsize=12, fontweight='bold')
            ax.set_title(f'{feature_names[feature]}敏感性分析', fontsize=14, fontweight='bold')
            ax.grid(axis='y', alpha=0.3)
            ax.set_ylim(0, max(df['录取概率']) * 1.2)

        plt.tight_layout()
        return fig

    def plot_comparison(self, students: List[Tuple[str, StudentProfile]],
                        applicant_pool: List[StudentProfile] = None,
                        figsize=(12, 6)):
        """
        绘制多个学生的录取概率对比图
        """
        df = self.model.compare_students(students, applicant_pool)

        fig, ax = plt.subplots(figsize=figsize)

        # 提取数值
        probabilities = [float(p.strip('%')) / 100 for p in df['录取概率']]

        bars = ax.barh(df['学生'], probabilities, color='coral', alpha=0.7)

        # 添加数值标签
        for idx, (bar, prob) in enumerate(zip(bars, probabilities)):
            ax.text(prob + 0.01, bar.get_y() + bar.get_height() / 2,
                    f'{prob:.1%}',
                    ha='left', va='center', fontsize=11, fontweight='bold')

        ax.set_xlabel('录取概率', fontsize=12, fontweight='bold')
        ax.set_title('学生录取概率对比', fontsize=14, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)
        ax.set_xlim(0, max(probabilities) * 1.15)

        plt.tight_layout()
        return fig

    def plot_competition_effect(self, student: StudentProfile,
                                max_pool_size: int = 20,
                                figsize=(12, 6)):
        """
        绘制竞争强度对录取概率的影响
        """
        # 创建不同竞争强度的申请池
        high_gpa_ratios = np.linspace(0, 1, 11)
        probabilities = []

        for ratio in high_gpa_ratios:
            # 构建申请池
            pool_size = max_pool_size
            high_gpa_count = int(pool_size * ratio)
            low_gpa_count = pool_size - high_gpa_count

            pool = [student]  # 包含当前学生

            # 添加高GPA学生
            for _ in range(high_gpa_count):
                pool.append(StudentProfile('A1', 'B2', 'C2', 'D2'))

            # 添加低GPA学生
            for _ in range(low_gpa_count):
                pool.append(StudentProfile('A3', 'B3', 'C3', 'D3'))

            result = self.model.calculate_admission_probability(student, pool)
            probabilities.append(result['admission_probability'])

        fig, ax = plt.subplots(figsize=figsize)

        ax.plot(high_gpa_ratios * 100, np.array(probabilities) * 100,
                marker='o', linewidth=2, markersize=8, color='darkgreen')

        ax.set_xlabel('申请池中高GPA学生比例 (%)', fontsize=12, fontweight='bold')
        ax.set_ylabel('录取概率 (%)', fontsize=12, fontweight='bold')
        ax.set_title('竞争强度对录取概率的影响', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)

        # 标注关键点
        ax.axvline(x=70, color='red', linestyle='--', alpha=0.5, label='高竞争阈值(70%)')
        ax.legend(fontsize=10)

        plt.tight_layout()
        return fig

    def plot_school_reputation_effect(self, base_gpa: str = 'A2',
                                      figsize=(10, 6)):
        """
        绘制学校信誉对GPA调整的影响
        """
        schools = ['D1', 'D2', 'D3', 'D4']
        school_names = ['顶尖国际学校', '知名国际学校', '一般国际学校', '其他学校']

        adjusted_gpas = []
        trust_factors = []

        for school in schools:
            adjusted, trust = self.model._adjust_gpa_by_school_reputation(base_gpa, school)
            adjusted_gpas.append(adjusted)
            trust_factors.append(trust)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

        # 信任系数
        bars1 = ax1.bar(school_names, trust_factors, color='skyblue', alpha=0.7)
        ax1.axhline(y=1.0, color='red', linestyle='--', alpha=0.5, label='基准线')
        ax1.set_ylabel('信任系数', fontsize=12, fontweight='bold')
        ax1.set_title('学校信誉信任系数', fontsize=13, fontweight='bold')
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)

        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width() / 2., height,
                     f'{height:.2f}',
                     ha='center', va='bottom', fontsize=10)

        # GPA调整
        gpa_order = {'A1': 4, 'A2': 3, 'A3': 2, 'A4': 1}
        adjusted_values = [gpa_order[gpa] for gpa in adjusted_gpas]

        bars2 = ax2.bar(school_names, adjusted_values, color='lightcoral', alpha=0.7)
        ax2.set_ylabel('调整后GPA等级', fontsize=12, fontweight='bold')
        ax2.set_title(f'原始GPA {base_gpa} 的调整结果', fontsize=13, fontweight='bold')
        ax2.set_yticks([1, 2, 3, 4])
        ax2.set_yticklabels(['A4', 'A3', 'A2', 'A1'])
        ax2.grid(axis='y', alpha=0.3)

        for bar, gpa in zip(bars2, adjusted_gpas):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width() / 2., height,
                     gpa,
                     ha='center', va='bottom', fontsize=11, fontweight='bold')

        plt.xticks(rotation=15, ha='right')
        plt.tight_layout()
        return fig