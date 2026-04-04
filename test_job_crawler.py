"""测试岗位爬虫 - 独立脚本"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("测试岗位数据爬取")
print("=" * 60)

try:
    from backend.vertical.career.real_job_data_integration import unified_job_service
    
    keyword = "Python工程师"
    location = "北京"
    limit = 5
    
    print(f"\n搜索: {keyword} @ {location}")
    print(f"获取数量: {limit}\n")
    
    jobs = unified_job_service.search_jobs(keyword, location, limit, use_cache=False)
    
    print(f"\n✓ 获取到 {len(jobs)} 个岗位\n")
    
    # 统计来源
    sources = {}
    for job in jobs:
        source = getattr(job, 'source', 'unknown')
        sources[source] = sources.get(source, 0) + 1
    
    print("数据来源:")
    source_names = {
        'boss_zhipin': '✓ BOSS直聘（真实数据）',
        'lagou': '✓ 拉勾网（真实数据）',
        'mock': '⚠ 模拟数据'
    }
    for source, count in sources.items():
        print(f"  {source_names.get(source, source)}: {count} 个")
    
    if jobs:
        print(f"\n示例岗位（前3个）:")
        for i, job in enumerate(jobs[:3], 1):
            print(f"\n  {i}. {job.title}")
            print(f"     公司: {job.company}")
            print(f"     薪资: {job.salary_min}-{job.salary_max}万")
            print(f"     技能: {', '.join(job.required_skills[:5])}")
            print(f"     来源: {getattr(job, 'source', 'unknown')}")
    
    print("\n" + "=" * 60)
    if 'boss_zhipin' in sources or 'lagou' in sources:
        print("✓ 成功：正在使用真实岗位数据！")
    else:
        print("⚠ 警告：当前使用模拟数据，真实爬虫可能遇到反爬限制")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ 错误: {e}")
    import traceback
    traceback.print_exc()
