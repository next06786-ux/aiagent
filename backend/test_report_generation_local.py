"""
本地测试报告生成功能
"""
import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
from dotenv import load_dotenv
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ 已加载环境变量: {env_path}")
else:
    print(f"⚠️  未找到 .env 文件: {env_path}")

from backend.llm.llm_service import LLMService
from backend.decision.report_generator import DecisionReportGenerator


async def test_report_generation():
    """测试报告生成"""
    print("=" * 60)
    print("测试报告生成功能")
    print("=" * 60)
    
    try:
        # 初始化 LLM 服务
        print("\n[1/4] 初始化 LLM 服务...")
        llm_service = LLMService()
        print(f"  ✅ LLM Provider: {os.getenv('LLM_PROVIDER', 'qwen')}")
        
        # 创建报告生成器
        print("[2/4] 创建报告生成器...")
        generator = DecisionReportGenerator(llm_service)
        print("  ✅ 报告生成器已创建")
        
        # 准备测试数据
        print("[3/4] 准备测试数据...")
        question = "我应该考研还是直接工作？"
        option_title = "入职腾讯，边工作边准备考研"
        option_description = "先积累工作经验，同时利用业余时间准备考研"
        
        agents_data = [
            {
                "id": "agent_1",
                "name": "理性分析师",
                "stance": "支持",
                "score": 82.5,
                "reasoning": "从职业发展角度看，这个选择兼顾了短期收益和长期规划。腾讯的工作经验对未来发展很有价值，同时保留了考研的可能性。"
            },
            {
                "id": "agent_2",
                "name": "冒险家",
                "stance": "中立",
                "score": 75.0,
                "reasoning": "这个选择相对保守，但也合理。如果能在工作中找到激情，也许就不需要考研了。"
            },
            {
                "id": "agent_3",
                "name": "实用主义者",
                "stance": "支持",
                "score": 88.0,
                "reasoning": "非常实用的选择。腾讯的薪资待遇好，可以解决经济问题，同时为考研做准备。即使最后不考研，也有了好的工作。"
            },
            {
                "id": "agent_4",
                "name": "理想主义者",
                "stance": "反对",
                "score": 65.0,
                "reasoning": "担心工作会占用太多精力，导致考研准备不充分。如果真的想考研，应该全力以赴。"
            },
            {
                "id": "agent_5",
                "name": "保守派",
                "stance": "支持",
                "score": 80.0,
                "reasoning": "这是一个稳妥的选择，既有保底的工作，又不放弃考研的机会。风险较低。"
            },
            {
                "id": "agent_6",
                "name": "社交导向者",
                "stance": "支持",
                "score": 78.0,
                "reasoning": "在腾讯工作可以建立良好的人脉网络，这对未来发展很重要。即使考研，这些人脉也会有帮助。"
            },
            {
                "id": "agent_7",
                "name": "创新者",
                "stance": "中立",
                "score": 72.0,
                "reasoning": "这个选择比较传统。如果能在工作中找到创新的机会，也许会有意想不到的收获。"
            }
        ]
        
        total_score = 77.1
        print(f"  ✅ 测试数据已准备 (7个Agent, 总分: {total_score})")
        
        # 生成报告
        print("[4/4] 开始生成报告...")
        print("-" * 60)
        
        result = await generator.generate_option_report(
            question=question,
            option_title=option_title,
            option_description=option_description,
            agents_data=agents_data,
            total_score=total_score
        )
        
        print("-" * 60)
        print("\n✅ 报告生成完成！")
        print("=" * 60)
        
        # 显示结果
        if result['success']:
            report = result['report']
            print("\n📊 报告内容：")
            print("=" * 60)
            
            print(f"\n【综合评分】{report['total_score']:.1f}/100")
            
            if report.get('summary'):
                print(f"\n【总体评价】")
                print(report['summary'])
            
            if report.get('key_insights'):
                print(f"\n【关键洞察】")
                for i, insight in enumerate(report['key_insights'], 1):
                    print(f"{i}. {insight}")
            
            if report.get('strengths'):
                print(f"\n【主要优势】")
                for i, strength in enumerate(report['strengths'], 1):
                    print(f"{i}. {strength}")
            
            if report.get('risks'):
                print(f"\n【潜在风险】")
                for i, risk in enumerate(report['risks'], 1):
                    print(f"{i}. {risk}")
            
            if report.get('recommendation'):
                print(f"\n【行动建议】")
                print(report['recommendation'])
            
            if report.get('agents_summary'):
                print(f"\n【Agent 评估汇总】")
                for agent in report['agents_summary']:
                    print(f"  • {agent['name']}: {agent['stance']} (评分: {agent['score']:.1f}, 信心: {agent['confidence']*100:.0f}%)")
            
            print("\n" + "=" * 60)
            print("✅ 测试成功！")
            
            # 显示完整文本（如果有）
            if report.get('full_text'):
                print("\n" + "=" * 60)
                print("📄 完整报告文本：")
                print("=" * 60)
                print(report['full_text'])
                print("=" * 60)
        else:
            print("\n⚠️  报告生成失败，返回备用报告")
            print(f"备用报告: {result['report']}")
            
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🚀 开始测试报告生成功能...\n")
    asyncio.run(test_report_generation())
    print("\n✅ 测试完成！\n")
