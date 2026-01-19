from bayesian_admission_model import BayesianAdmissionModel, StudentProfile
from visualization import AdmissionVisualizer
import matplotlib

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt


def example_1_basic_usage():
    """示例1: 基本使用 - 全优学生"""
    print("=" * 80)
    print("示例1: 基本使用 - 计算全优学生的录取概率")
    print("=" * 80)

    # 创建模型（目标：常春藤+）
    model = BayesianAdmissionModel(target_university_tier='ivy_plus')

    # 创建一个全优学生档案
    student = StudentProfile(
        # 学术表现
        gpa=3.98,
        sat_score=1580,
        ap_courses=12,
        ap_average_score=4.8,

        # 学术深度
        research_papers=2,
        research_projects=3,
        academic_competitions_national=2,
        academic_competitions_international=1,
        independent_projects=2,

        # 课外活动
        leadership_positions=3,
        community_service_hours=350,
        sports_achievements=3,
        arts_achievements=2,
        entrepreneurship=2,
        internships=2,

        # 个人品质
        recommendation_quality=9,
        essay_quality=9,

        # 背景
        school_tier=1,  # 顶尖国际学校
        school_college_matriculation_rate=0.85,
        legacy_status=False,
        first_generation=False,
        underrepresented_minority=False,
        special_talent=0
    )

    # 计算录取概率
    result = model.calculate_admission_probability(student, verbose=True)


def example_2_compare_different_profiles():
    """示例2: 比较不同类型的学生"""
    print("\n" + "=" * 80)
    print("示例2: 比较不同类型学生的录取概率")
    print("=" * 80 + "\n")

    model = BayesianAdmissionModel(target_university_tier='ivy_plus')

    # 创建多个不同类型的学生档案
    students = [
        ("学霸型-张三", StudentProfile(
            gpa=4.0, sat_score=1600, ap_courses=15, ap_average_score=5.0,
            research_papers=3, research_projects=4,
            academic_competitions_international=2, academic_competitions_national=3,
            independent_projects=3,
            leadership_positions=2, community_service_hours=200,
            sports_achievements=2, arts_achievements=1, entrepreneurship=1, internships=2,
            recommendation_quality=9, essay_quality=8,
            school_tier=1, school_college_matriculation_rate=0.90,
            legacy_status=False, first_generation=False,
            underrepresented_minority=False, special_talent=0
        )),

        ("科研型-李四", StudentProfile(
            gpa=3.92, sat_score=1540, ap_courses=10, ap_average_score=4.6,
            research_papers=5, research_projects=6,  # 科研突出
            academic_competitions_international=3, academic_competitions_national=4,
            independent_projects=5,
            leadership_positions=1, community_service_hours=150,
            sports_achievements=1, arts_achievements=1, entrepreneurship=0, internships=3,
            recommendation_quality=10, essay_quality=9,
            school_tier=2, school_college_matriculation_rate=0.75,
            legacy_status=False, first_generation=False,
            underrepresented_minority=False, special_talent=0
        )),

        ("领袖型-王五", StudentProfile(
            gpa=3.88, sat_score=1520, ap_courses=9, ap_average_score=4.4,
            research_papers=1, research_projects=2,
            academic_competitions_international=0, academic_competitions_national=1,
            independent_projects=1,
            leadership_positions=5, community_service_hours=500,  # 领导力突出
            sports_achievements=4, arts_achievements=3, entrepreneurship=3, internships=4,
            recommendation_quality=9, essay_quality=10,
            school_tier=2, school_college_matriculation_rate=0.70,
            legacy_status=False, first_generation=False,
            underrepresented_minority=False, special_talent=0
        )),

        ("特长型-赵六", StudentProfile(
            gpa=3.85, sat_score=1480, ap_courses=8, ap_average_score=4.2,
            research_papers=0, research_projects=1,
            academic_competitions_international=0, academic_competitions_national=0,
            independent_projects=1,
            leadership_positions=2, community_service_hours=180,
            sports_achievements=5, arts_achievements=0, entrepreneurship=0, internships=1,
            recommendation_quality=8, essay_quality=8,
            school_tier=2, school_college_matriculation_rate=0.65,
            legacy_status=False, first_generation=False,
            underrepresented_minority=False, special_talent=4  # 国家级体育特长
        )),

        ("多样性-孙七", StudentProfile(
            gpa=3.80, sat_score=1450, ap_courses=7, ap_average_score=4.0,
            research_papers=1, research_projects=2,
            academic_competitions_international=0, academic_competitions_national=1,
            independent_projects=2,
            leadership_positions=3, community_service_hours=300,
            sports_achievements=2, arts_achievements=2, entrepreneurship=2, internships=2,
            recommendation_quality=8, essay_quality=9,
            school_tier=3, school_college_matriculation_rate=0.50,
            legacy_status=True,  # 有校友关系
            first_generation=True,  # 第一代大学生
            underrepresented_minority=True,  # 少数族裔
            special_talent=0
        )),
    ]

    # 比较学生
    df = model.compare_students(students)
    print(df.to_string(index=False))

    # 可视化对比
    visualizer = AdmissionVisualizer(model)
    fig = visualizer.plot_comparison(students)
    plt.savefig('comparison_detailed.png', dpi=150, bbox_inches='tight')
    print("\n图表已保存为 comparison_detailed.png")
    plt.close()


def example_3_gpa_vs_holistic():
    """示例3: GPA vs 综合素质 - 谁更重要？"""
    print("\n" + "=" * 80)
    print("示例3: 高GPA低综合 vs 低GPA高综合")
    print("=" * 80 + "\n")

    model = BayesianAdmissionModel(target_university_tier='top')

    # 学生A: 高GPA，但其他方面一般
    student_a = StudentProfile(
        gpa=4.0, sat_score=1600, ap_courses=15, ap_average_score=5.0,
        research_papers=0, research_projects=1,
        academic_competitions_international=0, academic_competitions_national=0,
        independent_projects=0,
        leadership_positions=1, community_service_hours=50,
        sports_achievements=1, arts_achievements=0, entrepreneurship=0, internships=0,
        recommendation_quality=6, essay_quality=6,
        school_tier=2, school_college_matriculation_rate=0.60,
        legacy_status=False, first_generation=False,
        underrepresented_minority=False, special_talent=0
    )

    # 学生B: GPA略低，但综合素质强
    student_b = StudentProfile(
        gpa=3.85, sat_score=1520, ap_courses=10, ap_average_score=4.5,
        research_papers=3, research_projects=4,
        academic_competitions_international=2, academic_competitions_national=3,
        independent_projects=4,
        leadership_positions=4, community_service_hours=400,
        sports_achievements=3, arts_achievements=3, entrepreneurship=2, internships=3,
        recommendation_quality=10, essay_quality=10,
        school_tier=2, school_college_matriculation_rate=0.70,
        legacy_status=False, first_generation=False,
        underrepresented_minority=False, special_talent=0
    )

    result_a = model.calculate_admission_probability(student_a, verbose=False)
    result_b = model.calculate_admission_probability(student_b, verbose=False)

    print("学生A (高GPA低综合):")
    print(f"  GPA: {student_a.gpa}, SAT: {student_a.sat_score}")
    print(f"  科研: {student_a.research_papers}篇论文, {student_a.research_projects}个项目")
    print(f"  领导力: {student_a.leadership_positions}个职位")
    print(f"  录取概率: {result_a['admission_probability']:.2%}")
    print(f"  综合分: {result_a['weighted_score']:.1f}/100\n")

    print("学生B (GPA略低但综合强):")
    print(f"  GPA: {student_b.gpa}, SAT: {student_b.sat_score}")
    print(f"  科研: {student_b.research_papers}篇论文, {student_b.research_projects}个项目")
    print(f"  领导力: {student_b.leadership_positions}个职位")
    print(f"  录取概率: {result_b['admission_probability']:.2%}")
    print(f"  综合分: {result_b['weighted_score']:.1f}/100\n")

    if result_b['admission_probability'] > result_a['admission_probability']:
        print("结论: 在顶尖大学申请中，综合素质可以弥补GPA的不足！")
    else:
        print("结论: GPA仍然是最重要的基础指标。")


def example_4_competition_intensity():
    """示例4: 竞争强度的影响"""
    print("\n" + "=" * 80)
    print("示例4: 竞争强度对录取概率的影响")
    print("=" * 80 + "\n")

    model = BayesianAdmissionModel(target_university_tier='ivy_plus')

    # 创建一个优秀学生
    student = StudentProfile(
        gpa=3.95, sat_score=1560, ap_courses=12, ap_average_score=4.7,
        research_papers=2, research_projects=3,
        academic_competitions_international=1, academic_competitions_national=2,
        independent_projects=2,
        leadership_positions=3, community_service_hours=250,
        sports_achievements=3, arts_achievements=2, entrepreneurship=1, internships=2,
        recommendation_quality=9, essay_quality=8,
        school_tier=1, school_college_matriculation_rate=0.80,
        legacy_status=False, first_generation=False,
        underrepresented_minority=False, special_talent=0
    )

    # 场景1: 低竞争环境（申请池中学生水平一般）
    low_competition_pool = [student]
    for i in range(20):
        low_competition_pool.append(StudentProfile(
            gpa=3.6, sat_score=1400, ap_courses=5, ap_average_score=3.8,
            research_papers=0, research_projects=1,
            academic_competitions_international=0, academic_competitions_national=0,
            independent_projects=0,
            leadership_positions=1, community_service_hours=100,
            sports_achievements=1, arts_achievements=1, entrepreneurship=0, internships=0,
            recommendation_quality=6, essay_quality=6,
            school_tier=3, school_college_matriculation_rate=0.40,
            legacy_status=False, first_generation=False,
            underrepresented_minority=False, special_talent=0
        ))

    # 场景2: 高竞争环境（申请池中都是学霸）
    high_competition_pool = [student]
    for i in range(20):
        high_competition_pool.append(StudentProfile(
            gpa=3.98, sat_score=1580, ap_courses=14, ap_average_score=4.9,
            research_papers=3, research_projects=4,
            academic_competitions_international=2, academic_competitions_national=3,
            independent_projects=3,
            leadership_positions=3, community_service_hours=300,
            sports_achievements=3, arts_achievements=2, entrepreneurship=2, internships=2,
            recommendation_quality=9, essay_quality=9,
            school_tier=1, school_college_matriculation_rate=0.85,
            legacy_status=False, first_generation=False,
            underrepresented_minority=False, special_talent=0
        ))

    result_low = model.calculate_admission_probability(student, low_competition_pool)
    result_high = model.calculate_admission_probability(student, high_competition_pool)

    print(f"低竞争环境:")
    print(f"  申请池平均学术分: ~60分")
    print(f"  学术权重调整: ×{result_low['competition_adjustment']['academic_adjustment']:.2f}")
    print(f"  录取概率: {result_low['admission_probability']:.2%}\n")

    print(f"高竞争环境:")
    print(f"  申请池平均学术分: ~95分")
    print(f"  学术权重调整: ×{result_high['competition_adjustment']['academic_adjustment']:.2f}")
    print(f"  录取概率: {result_high['admission_probability']:.2%}\n")

    print(f"概率下降: {(result_low['admission_probability'] - result_high['admission_probability']):.2%}")
    print(f"结论: 在高竞争环境下，学术优势被削弱，其他维度变得更重要！")


def example_5_school_reputation():
    """示例5: 学校背景的影响"""
    print("\n" + "=" * 80)
    print("示例5: 学校背景对录取概率的影响")
    print("=" * 80 + "\n")

    model = BayesianAdmissionModel(target_university_tier='top')

    # 相同的学生特征，不同的学校背景
    base_profile = {
        'gpa': 3.90,
        'sat_score': 1540,
        'ap_courses': 10,
        'ap_average_score': 4.5,
        'research_papers': 2,
        'research_projects': 3,
        'academic_competitions_international': 1,
        'academic_competitions_national': 2,
        'independent_projects': 2,
        'leadership_positions': 2,
        'community_service_hours': 200,
        'sports_achievements': 2,
        'arts_achievements': 2,
        'entrepreneurship': 1,
        'internships': 2,
        'recommendation_quality': 8,
        'essay_quality': 8,
        'legacy_status': False,
        'first_generation': False,
        'underrepresented_minority': False,
        'special_talent': 0
    }

    schools = [
        ("顶尖国际学校(Tier 1)", 1, 0.90),
        ("知名国际学校(Tier 2)", 2, 0.75),
        ("一般国际学校(Tier 3)", 3, 0.55),
        ("普通国际学校(Tier 4)", 4, 0.35),
        ("其他学校(Tier 5)", 5, 0.20),
    ]

    print("相同学生特征 (GPA 3.90, SAT 1540)，不同学校背景的录取概率:\n")

    for school_name, tier, matriculation_rate in schools:
        student = StudentProfile(
            **base_profile,
            school_tier=tier,
            school_college_matriculation_rate=matriculation_rate
        )
        result = model.calculate_admission_probability(student)

        print(f"{school_name:25s} | 调整后GPA: {result['adjusted_gpa']:.2f} | "
              f"信任系数: {result['school_trust_multiplier']:.2f} | "
              f"学术分: {result['dimension_scores']['academic_excellence']:.1f} | "
              f"录取概率: {result['admission_probability']:.2%}")

    print("\n结论: 学校背景通过影响GPA可信度和历史录取率，显著影响录取概率！")


def example_6_special_talent():
    """示例6: 特殊才能的加成"""
    print("\n" + "=" * 80)
    print("示例6: 特殊才能对录取概率的影响")
    print("=" * 80 + "\n")

    model = BayesianAdmissionModel(target_university_tier='ivy_plus')

    # 基础学生（学术一般）
    base_student = StudentProfile(
        gpa=3.70, sat_score=1450, ap_courses=6, ap_average_score=4.0,
        research_papers=0, research_projects=1,
        academic_competitions_international=0, academic_competitions_national=0,
        independent_projects=1,
        leadership_positions=1, community_service_hours=100,
        sports_achievements=1, arts_achievements=1, entrepreneurship=0, internships=1,
        recommendation_quality=7, essay_quality=7,
        school_tier=3, school_college_matriculation_rate=0.50,
        legacy_status=False, first_generation=False,
        underrepresented_minority=False, special_talent=0
    )

    # 有世界级特殊才能的学生（如奥运选手）
    talented_student = StudentProfile(
        gpa=3.70, sat_score=1450, ap_courses=6, ap_average_score=4.0,
        research_papers=0, research_projects=1,
        academic_competitions_international=0, academic_competitions_national=0,
        independent_projects=1,
        leadership_positions=1, community_service_hours=100,
        sports_achievements=5, arts_achievements=1, entrepreneurship=0, internships=1,
        recommendation_quality=7, essay_quality=7,
        school_tier=3, school_college_matriculation_rate=0.50,
        legacy_status=False, first_generation=False,
        underrepresented_minority=False, special_talent=5  # 世界级
    )

    result_base = model.calculate_admission_probability(base_student)
    result_talented = model.calculate_admission_probability(talented_student)

    print("普通学生 (学术一般):")
    print(f"  GPA: {base_student.gpa}, SAT: {base_student.sat_score}")
    print(f"  特殊才能: {base_student.special_talent}级")
    print(f"  录取概率: {result_base['admission_probability']:.2%}\n")

    print("特殊才能学生 (相同学术，世界级体育特长):")
    print(f"  GPA: {talented_student.gpa}, SAT: {talented_student.sat_score}")
    print(f"  特殊才能: {talented_student.special_talent}级 (世界级)")
    print(f"  录取概率: {result_talented['admission_probability']:.2%}\n")

    print(f"概率提升: {(result_talented['admission_probability'] - result_base['admission_probability']):.2%}")
    print(f"提升倍数: {result_talented['admission_probability'] / result_base['admission_probability']:.1f}x")
    print("\n结论: 世界级特殊才能可以极大提升录取概率，甚至弥补学术上的不足！")


def example_7_different_university_tiers():
    """示例7: 同一学生申请不同层级大学"""
    print("\n" + "=" * 80)
    print("示例7: 同一学生申请不同层级大学的录取概率")
    print("=" * 80 + "\n")

    # 创建一个中上水平的学生
    student = StudentProfile(
        gpa=3.85, sat_score=1520, ap_courses=9, ap_average_score=4.4,
        research_papers=1, research_projects=2,
        academic_competitions_international=0, academic_competitions_national=1,
        independent_projects=2,
        leadership_positions=2, community_service_hours=200,
        sports_achievements=2, arts_achievements=2, entrepreneurship=1, internships=2,
        recommendation_quality=8, essay_quality=8,
        school_tier=2, school_college_matriculation_rate=0.70,
        legacy_status=False, first_generation=False,
        underrepresented_minority=False, special_talent=0
    )

    tiers = [
        ('ivy_plus', '常春藤+ (哈佛/斯坦福/MIT等)'),
        ('top', 'Top 20 大学'),
        ('elite', 'Top 50 大学'),
        ('good', 'Top 100 大学')
    ]

    print("学生档案: GPA 3.85, SAT 1520, 中上水平综合素质\n")

    for tier, name in tiers:
        model = BayesianAdmissionModel(target_university_tier=tier)
        result = model.calculate_admission_probability(student)
        print(f"{name:35s} | 先验录取率: {result['prior_admission']:5.1%} | "
              f"录取概率: {result['admission_probability']:6.2%} | "
              f"综合分: {result['weighted_score']:.1f}")

    print("\n结论: 合理定位目标大学层级，匹配自身实力！")


def example_8_legacy_and_diversity():
    """示例8: 校友关系和多样性因素"""
    print("\n" + "=" * 80)
    print("示例8: 校友关系和多样性因素的影响")
    print("=" * 80 + "\n")

    model = BayesianAdmissionModel(target_university_tier='ivy_plus')

    # 基准学生
    base = StudentProfile(
        gpa=3.80, sat_score=1480, ap_courses=8, ap_average_score=4.2,
        research_papers=1, research_projects=2,
        academic_competitions_international=0, academic_competitions_national=1,
        independent_projects=1,
        leadership_positions=2, community_service_hours=150,
        sports_achievements=2, arts_achievements=2, entrepreneurship=1, internships=1,
        recommendation_quality=7, essay_quality=7,
        school_tier=2, school_college_matriculation_rate=0.65,
        legacy_status=False, first_generation=False,
        underrepresented_minority=False, special_talent=0
    )

    # 有校友关系
    legacy = StudentProfile(
        gpa=3.80, sat_score=1480, ap_courses=8, ap_average_score=4.2,
        research_papers=1, research_projects=2,
        academic_competitions_international=0, academic_competitions_national=1,
        independent_projects=1,
        leadership_positions=2, community_service_hours=150,
        sports_achievements=2, arts_achievements=2, entrepreneurship=1, internships=1,
        recommendation_quality=7, essay_quality=7,
        school_tier=2, school_college_matriculation_rate=0.65,
        legacy_status=True,  # 校友关系
        first_generation=False,
        underrepresented_minority=False, special_talent=0
    )

    # 多样性学生
    diversity = StudentProfile(
        gpa=3.80, sat_score=1480, ap_courses=8, ap_average_score=4.2,
        research_papers=1, research_projects=2,
        academic_competitions_international=0, academic_competitions_national=1,
        independent_projects=1,
        leadership_positions=2, community_service_hours=150,
        sports_achievements=2, arts_achievements=2, entrepreneurship=1, internships=1,
        recommendation_quality=7, essay_quality=7,
        school_tier=2, school_college_matriculation_rate=0.65,
        legacy_status=False,
        first_generation=True,  # 第一代大学生
        underrepresented_minority=True,  # 少数族裔
        special_talent=0
    )

    result_base = model.calculate_admission_probability(base)
    result_legacy = model.calculate_admission_probability(legacy)
    result_diversity = model.calculate_admission_probability(diversity)

    print("基准学生:")
    print(f"  背景分: {result_base['dimension_scores']['background_context']:.1f}")
    print(f"  录取概率: {result_base['admission_probability']:.2%}\n")

    print("校友关系学生 (Legacy):")
    print(f"  背景分: {result_legacy['dimension_scores']['background_context']:.1f}")
    print(f"  录取概率: {result_legacy['admission_probability']:.2%}")
    print(f"  提升: {(result_legacy['admission_probability'] - result_base['admission_probability']):.2%}\n")

    print("多样性学生 (第一代+少数族裔):")
    print(f"  背景分: {result_diversity['dimension_scores']['background_context']:.1f}")
    print(f"  录取概率: {result_diversity['admission_probability']:.2%}")
    print(f"  提升: {(result_diversity['admission_probability'] - result_base['admission_probability']):.2%}\n")

    print("结论: 校友关系和多样性因素在常春藤录取中有显著影响！")


def example_9_comprehensive_analysis():
    """示例9: 综合案例分析"""
    print("\n" + "=" * 80)
    print("示例9: 真实案例综合分析")
    print("=" * 80 + "\n")

    model = BayesianAdmissionModel(target_university_tier='ivy_plus')

    # 案例: 一个真实的申请者
    student = StudentProfile(
        gpa=3.92,
        sat_score=1550,
        ap_courses=11,
        ap_average_score=4.6,

        research_papers=2,
        research_projects=3,
        academic_competitions_international=1,
        academic_competitions_national=2,
        independent_projects=3,

        leadership_positions=4,
        community_service_hours=320,
        sports_achievements=3,
        arts_achievements=2,
        entrepreneurship=2,
        internships=2,

        recommendation_quality=9,
        essay_quality=9,

        school_tier=1,
        school_college_matriculation_rate=0.82,
        legacy_status=False,
        first_generation=False,
        underrepresented_minority=False,
        special_talent=0
    )

    # 详细分析
    result = model.calculate_admission_probability(student, verbose=True)

    # 给出改进建议
    print("\n【改进建议】")
    scores = result['dimension_scores']

    if scores['academic_excellence'] < 85:
        print("  ⚠ 学术卓越度可提升: 考虑提高标化成绩或增加AP课程")
    if scores['intellectual_curiosity'] < 70:
        print("  ⚠ 学术深度可提升: 增加科研论文或参加更多学术竞赛")
    if scores['extracurricular_impact'] < 70:
        print("  ⚠ 课外活动影响力可提升: 争取更多领导职位或深化现有活动")
    if scores['personal_qualities'] < 80:
        print("  ⚠ 个人品质展示可提升: 优化文书，争取更强推荐信")

    if all(score >= 80 for score in scores.values()):
        print("  ✓ 各维度表现均衡优秀，继续保持！")


if __name__ == "__main__":
    # 运行所有示例
    example_1_basic_usage()
    # example_2_compare_different_profiles()
    # example_3_gpa_vs_holistic()
    # example_4_competition_intensity()
    # example_5_school_reputation()
    # example_6_special_talent()
    # example_7_different_university_tiers()
    # example_8_legacy_and_diversity()
    # example_9_comprehensive_analysis()

    print("\n" + "=" * 80)
    print("所有示例运行完成！")
    print("=" * 80)