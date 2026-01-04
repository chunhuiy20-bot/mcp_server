import asyncio

from agent.test.TestGetUserChatList import XiaoZhiAPIClient
from schemas.ybbl.ai_school.vo.PersonalityReportVo import TalentReportResponse, IdentityVO, MbtiVO, CoreCompetencyVO, \
    PersonalityVO, BigFiveScoresVO, SummaryVO, PersonalityTag, SubDimensionVO, MetricVO, StrengthSimpleVO, StrengthKey


def create_test_profile():
    """创建测试用的完整用户画像数据"""
    return TalentReportResponse(
        user_id='2',
        identity=IdentityVO(
            mbti=MbtiVO(code='INTJ', label='战略家'),
            core_competencies=[
                CoreCompetencyVO(id=1, label='学习型成长者'),
                CoreCompetencyVO(id=2, label='情感支持者'),
                CoreCompetencyVO(id=3, label='理性分析者')
            ]
        ),
        personality=PersonalityVO(
            big_five_scores=BigFiveScoresVO(
                openness=90,
                conscientiousness=85,
                extraversion=40,
                agreeableness=75,
                stability=70
            ),
            summary=SummaryVO(
                title='安静且开放的探索者',
                tags=[
                    PersonalityTag(label='内向自省', color='#6C7A89'),
                    PersonalityTag(label='开放好奇', color='#3498DB'),
                    PersonalityTag(label='理性计划', color='#27AE60'),
                    PersonalityTag(label='温暖支持', color='#F7CA18'),
                    PersonalityTag(label='主动自驱', color='#E67E22')
                ],
                description='你展现出"安静的探索者"气质，喜欢独处并善于自我调节情绪，能在复杂环境中保持内心稳定。你对新知充满好奇，乐于学习和尝试，开放性强，面对变化虽有短暂不适但能主动应对。思维方式兼具理性与感性，既重视逻辑分析，也能在亲密关系中用温暖情感连接他人。你做事有计划，喜欢提前安排，动力来源于对新鲜事物的热情和对成果的期待。团队合作时，你倾向于用关心和支持影响他人，营造温暖氛围。面对不确定性，你果断制定策略并主动行动，保持掌控感。整体来看，你是一个内心丰富、行动主动、既理性又温暖的人，善于自我成长，也能温柔影响身边的人。'
            ),
            sub_dimensions=[
                SubDimensionVO(
                    metrics=[
                        MetricVO(metric_type=1, list_value=[40, 80]),
                        MetricVO(metric_type=2, list_value=[85, 75])
                    ]
                )
            ]
        ),
        clifton_strengths=[
            StrengthSimpleVO(key=StrengthKey.LEARNER, score=95, rank=1),
            StrengthSimpleVO(key=StrengthKey.INPUT, score=90, rank=2),
            StrengthSimpleVO(key=StrengthKey.EMPATHY, score=88, rank=3),
            StrengthSimpleVO(key=StrengthKey.STRATEGIC, score=85, rank=4),
            StrengthSimpleVO(key=StrengthKey.DELIBERATIVE, score=80, rank=5),
            StrengthSimpleVO(key=StrengthKey.RESPONSIBILITY, score=78, rank=6),
            StrengthSimpleVO(key=StrengthKey.ARRANGER, score=75, rank=7),
            StrengthSimpleVO(key=StrengthKey.POSITIVITY, score=73, rank=8),
            StrengthSimpleVO(key=StrengthKey.HARMONY, score=70, rank=9),
            StrengthSimpleVO(key=StrengthKey.ACHIEVER, score=68, rank=10),
            StrengthSimpleVO(key=StrengthKey.ANALYTICAL, score=65, rank=11),
            StrengthSimpleVO(key=StrengthKey.CONTEXT, score=63, rank=12),
            StrengthSimpleVO(key=StrengthKey.FUTURISTIC, score=60, rank=13),
            StrengthSimpleVO(key=StrengthKey.DEVELOPER, score=58, rank=14),
            StrengthSimpleVO(key=StrengthKey.DISCIPLINE, score=55, rank=15),
            StrengthSimpleVO(key=StrengthKey.FOCUS, score=53, rank=16),
            StrengthSimpleVO(key=StrengthKey.RESTORATIVE, score=50, rank=17),
            StrengthSimpleVO(key=StrengthKey.COMMAND, score=48, rank=18),
            StrengthSimpleVO(key=StrengthKey.SELF_ASSURANCE, score=45, rank=19),
            StrengthSimpleVO(key=StrengthKey.SIGNIFICANCE, score=43, rank=20),
            StrengthSimpleVO(key=StrengthKey.WOO, score=40, rank=21),
            StrengthSimpleVO(key=StrengthKey.COMPETITION, score=38, rank=22),
            StrengthSimpleVO(key=StrengthKey.MAXIMIZER, score=35, rank=23),
            StrengthSimpleVO(key=StrengthKey.INCLUDER, score=33, rank=24),
            StrengthSimpleVO(key=StrengthKey.INDIVIDUALIZATION, score=30, rank=25),
            StrengthSimpleVO(key=StrengthKey.CONSISTENCY, score=28, rank=26),
            StrengthSimpleVO(key=StrengthKey.COMMUNICATION, score=25, rank=27),
            StrengthSimpleVO(key=StrengthKey.IDEATION, score=23, rank=28),
            StrengthSimpleVO(key=StrengthKey.INTELLECTION, score=20, rank=29),
            StrengthSimpleVO(key=StrengthKey.ACTIVATOR, score=18, rank=30),
            StrengthSimpleVO(key=StrengthKey.CONNECTEDNESS, score=15, rank=31),
            StrengthSimpleVO(key=StrengthKey.ADAPTABILITY, score=13, rank=32),
            StrengthSimpleVO(key=StrengthKey.BELIEF, score=10, rank=33),
            StrengthSimpleVO(key=StrengthKey.RELATOR, score=8, rank=34)
        ]
    )


async def main():
    # 初始化客户端
    client = XiaoZhiAPIClient(
        base_url="http://47.107.82.252:8002",
        token="2a315992-6278-4bfb-ad34-62644953a725"
    )

    # 创建测试数据
    print("创建测试用户画像数据...")
    profile = create_test_profile()

    # 提交到后端
    print("\n开始提交用户画像到后端...")
    try:
        result = await client.submit_user_profile(profile)
        print("\n" + "=" * 60)
        print("提交成功!")
        print("=" * 60)
        print(f"返回结果: {result}")
    except Exception as e:
        print("\n" + "=" * 60)
        print("提交失败!")
        print("=" * 60)
        print(f"错误信息: {e}")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
