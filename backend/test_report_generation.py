"""
测试决策报告生成功能
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到 Python 路径
backend_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(backend_dir)
sys.path.insert(0, project_dir)
sys.path.insert(0, backend_dir)

from backend.decision.report_generator import DecisionReportGenerator
from backend.llm.llm_service import LLMService

async def test_report_generation():
    """测试报告生成"""
    
    print("="*60)
    print("测试决策报告生成功能")
    print("="*60)
    print()
    
    # 初始化 LLM 服务
    print("1. 初始化 LLM 服务...")
    llm_service = LLMService()
    print("   ✅ LLM 服务初始化成功")
    print()
    
    # 创建报告生成器
    print("2. 创建报告生成器...")
    generator = DecisionReportGenerator(llm_service)
    print("   ✅ 报告生成器创建成功")
    print()
    
    # 准备测试数据
    print("3. 准备测试数据...")
    question = "大学毕业后是先工作还是继续深造？"
    option_title = "先入职腾讯，半年后申请转岗到AI部门"
    option_description = "9月入职腾讯，先在普通开发岗位工作，熟悉公司流程和业务。计划在入职半年后提交内部转岗申请，目标是AI相关部门。"
    
    agents_data = [
        {
            "id": "rational_analyst",
            "name": "理性分析师",
            "stance": "支持 (85分)",
            "score": 85,
            "reasoning": "从职业发展角度看，这个选择兼顾了稳定性和成长性。腾讯的平台优势明显，内部转岗机制相对成熟。"
        },
        {
            "id": "adventurer",
            "name": "冒险家",
            "score": 80,
            "stance": "支持 (80分)",
            "reasoning": "虽然不是最激进的选择，但保留了足够的灵活性。半年时间足够评估是否适合AI方向。"
        },
        {
            "id": "pragmatist",
            "name": "实用主义者",
            "score": 88,
            "stance": "强烈支持 (88分)",
            "reasoning": "这是最务实的选择。先有稳定收入，再寻求发展机会。风险可控，收益可期。"
        },
        {
            "id": "idealist",
            "name": "理想主义者",
            "score": 75,
            "stance": "中立偏支持 (75分)",
            "reasoning": "虽然不是直接追求理想，但为实现AI梦想铺路。需要确保不会在舒适区停滞。"
        },
        {
            "id": "conservative",
            "name": "保守派",
            "score": 90,
            "stance": "强烈支持 (90分)",
            "reasoning": "这是最稳妥的选择。大厂背景、稳定收入、内部机会，风险最小化。"
        },
        {
            "id": "social_navigator",
            "name": "社交导向者",
            "score": 87,
            "stance": "支持 (87分)",
            "reasoning": "腾讯的人脉资源和品牌价值不可估量。内部转岗比外部跳槽更容易获得支持。"
        },
        {
            "id": "innovator",
            "name": "创新者",
            "score": 78,
            "stance": "支持 (78分)",
            "reasoning": "虽然初期岗位可能不够创新，但腾讯的AI部门有很多前沿项目。关键是要主动寻找机会。"
        }
    ]
    
    total_score = sum(a["score"] for a in agents_data) / len(agents_data)
    
    print(f"   问题: {question}")
    print(f"   选项: {option_title}")
    print(f"   Agent数量: {len(agents_data)}")
    print(f"   总分: {total_score:.1f}")
    print()
    
    # 生成报告
    print("4. 生成决策报告...")
    print("   (这可能需要几秒钟，请稍候...)")
    print()
    
    try:
        result = await generator.generate_option_report(
            question=question,
            option_title=option_title,
            option_description=option_description,
            agents_data=agents_data,
            total_score=total_score
        )
        
        if result.get("success"):
            print("   ✅ 报告生成成功！")
            print()
            print("="*60)
            print("报告内容预览")
            print("="*60)
            print()
            
            report = result.get("report", {})
            
            # 总结
            print("【总结】")
            print(report.get("summary", "无"))
            print()
            
            # 关键洞察
            print("【关键洞察】")
            for i, insight in enumerate(report.get("key_insights", []), 1):
                print(f"{i}. {insight}")
            print()
            
            # 优势
            print("【优势】")
            for i, strength in enumerate(report.get("strengths", []), 1):
                print(f"{i}. {strength}")
            print()
            
            # 风险
            print("【风险】")
            for i, risk in enumerate(report.get("risks", []), 1):
                print(f"{i}. {risk}")
            print()
            
            # 建议
            print("【建议】")
            print(report.get("recommendation", "无"))
            print()
            
            # Agent汇总
            print("【Agent评分汇总】")
            for agent in report.get("agents_summary", []):
                print(f"  • {agent.get('name')}: {agent.get('stance')} - {agent.get('score')}分")
            print()
            
            print(f"【综合评分】{report.get('total_score', 0):.1f} 分")
            print()
            
            # 完整文本
            if report.get("full_text"):
                print("="*60)
                print("完整报告文本")
                print("="*60)
                print()
                print(report.get("full_text"))
                print()
            
        else:
            print("   ❌ 报告生成失败")
            print(f"   错误: {result.get('error', '未知错误')}")
            
    except Exception as e:
        print(f"   ❌ 报告生成异常: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("="*60)
    print("测试完成")
    print("="*60)

if __name__ == '__main__':
    asyncio.run(test_report_generation())
