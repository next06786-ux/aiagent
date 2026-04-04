"""测试BOSS直聘爬虫是否正常工作

运行方式：
  从项目根目录运行: python backend/test_boss_crawler.py
  或从backend目录运行: python -m test_boss_crawler
"""
import sys
import os

# 确保能找到backend模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from backend.vertical.career.real_job_data_integration import unified_job_service
except ImportError:
    # 如果从backend目录运行，尝试直接导入
    from vertical.career.real_job_data_integration import unified_job_service

print("=" * 60)
print("测试BOSS直聘爬虫")
print("=" * 60)

# 搜索Python工程师岗位
keyword = "Python工程师"
location = "北京"
limit = 5

print(f"\n搜索关键词: {keyword}")
print(f"地点: {location}")
print(f"数量: {limit}\n")

jobs = unified_job_service.search_jobs(keyword, location, limit, use_cache=False)

print(f"\n获取到 {len(jobs)} 个岗位:\n")

# 统计数据来源
sources = {}
for job in jobs:
    source = getattr(job, 'source', 'unknown')
    sources[source] = sources.get(source, 0) + 1

print("数据来源统计:")
for source, count in sources.items():
    source_names = {
        'boss_zhipin': 'BOSS直聘',
        'lagou': '拉勾网',
        'mock': '模拟数据'
    }
    print(f"  {source_names.get(source, source)}: {count} 个")

print("\n岗位详情:")
for i, job in enumerate(jobs[:3], 1):
    print(f"\n{i}. {job.title}")
    print(f"   公司: {job.company}")
    print(f"   薪资: {job.salary_min}-{job.salary_max}万")
    print(f"   地点: {job.location}")
    print(f"   技能: {', '.join(job.required_skills[:5])}")
    print(f"   来源: {getattr(job, 'source', 'unknown')}")
    if hasattr(job, 'source_url') and job.source_url:
        print(f"   链接: {job.source_url}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
