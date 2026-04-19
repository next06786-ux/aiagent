"""
初始化树洞测试数据
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uuid
from backend.social.tree_hole_storage import get_tree_hole_storage


def init_test_data():
    """初始化测试数据"""
    storage = get_tree_hole_storage()
    
    # 创建树洞
    tree_holes = [
        {"id": "1", "title": "心情树洞", "description": "分享你的心情和感受"},
        {"id": "2", "title": "秘密树洞", "description": "说出你不敢说的秘密"},
        {"id": "3", "title": "梦想树洞", "description": "分享你的梦想和目标"},
        {"id": "4", "title": "烦恼树洞", "description": "倾诉你的烦恼和困扰"},
        {"id": "5", "title": "感恩树洞", "description": "感谢生活中的美好"},
    ]
    
    print("=" * 60)
    print("开始初始化树洞数据...")
    print("=" * 60)
    
    print("\n1. 创建树洞...")
    test_user_id = "test_user_001"
    for hole in tree_holes:
        success = storage.create_tree_hole(hole["id"], test_user_id, hole["title"], hole["description"])
        if success:
            print(f"  ✓ {hole['title']} - {hole['description']}")
        else:
            print(f"  ✗ {hole['title']} 创建失败")
    
    # 添加测试消息
    test_messages = [
        # 心情树洞 - 职场相关
        {"tree_hole_id": "1", "content": "今天工作压力好大，老板又加了新需求，要不要跳槽呢？感觉身心俱疲"},
        {"tree_hole_id": "1", "content": "最近失眠严重，每天都在想工作的事情，是不是该换个工作环境了"},
        {"tree_hole_id": "1", "content": "和同事关系处理不好，感觉很孤独，要不要主动改善关系"},
        {"tree_hole_id": "1", "content": "今天被领导批评了，心情很低落，不知道该怎么调整"},
        {"tree_hole_id": "1", "content": "工作三年了，感觉没有成长，很迷茫"},
        
        # 秘密树洞 - 情感和职业选择
        {"tree_hole_id": "2", "content": "暗恋同事很久了，要不要表白？担心被拒绝后工作会很尴尬"},
        {"tree_hole_id": "2", "content": "其实我一直想换工作，但不敢跟家人说，怕他们担心"},
        {"tree_hole_id": "2", "content": "想辞职创业，但担心失败后没有退路，家里还有房贷要还"},
        {"tree_hole_id": "2", "content": "我在两家公司的offer之间纠结，一个钱多但加班，一个轻松但工资低"},
        {"tree_hole_id": "2", "content": "其实我不喜欢现在的专业，但已经工作了，不知道还能不能转行"},
        
        # 梦想树洞 - 人生目标
        {"tree_hole_id": "3", "content": "我的梦想是环游世界，要不要辞职去旅行？但存款不多"},
        {"tree_hole_id": "3", "content": "想考研深造，但担心年龄太大了，而且工作也不错"},
        {"tree_hole_id": "3", "content": "想转行做程序员，但零基础不知道能不能成功，已经28岁了"},
        {"tree_hole_id": "3", "content": "梦想是开一家咖啡店，但不知道从何开始，需要多少资金"},
        {"tree_hole_id": "3", "content": "想出国留学，但家里经济条件一般，要不要贷款"},
        
        # 烦恼树洞 - 生活压力
        {"tree_hole_id": "4", "content": "房租又涨了，要不要换个便宜的地方？但通勤会变远"},
        {"tree_hole_id": "4", "content": "父母催婚，但我还没准备好，也没遇到合适的人"},
        {"tree_hole_id": "4", "content": "工作和生活平衡不了，要不要降薪换个轻松的工作？"},
        {"tree_hole_id": "4", "content": "信用卡欠了很多，压力很大，要不要跟家人坦白"},
        {"tree_hole_id": "4", "content": "健康检查出了问题，要不要辞职休养？但没有收入怎么办"},
        
        # 感恩树洞 - 积极经历
        {"tree_hole_id": "5", "content": "今天终于下定决心辞职了，感觉很轻松，感谢自己的勇气"},
        {"tree_hole_id": "5", "content": "成功转行了，虽然过程很艰难，但感谢当初勇敢的自己"},
        {"tree_hole_id": "5", "content": "终于还清了所有债务，感觉人生又有了希望"},
        {"tree_hole_id": "5", "content": "今天收到了心仪公司的offer，感谢这段时间的努力"},
        {"tree_hole_id": "5", "content": "和家人坦白了自己的想法，他们很支持我，感动"},
    ]
    
    print("\n2. 添加测试消息...")
    success_count = 0
    for msg in test_messages:
        message_id = str(uuid.uuid4())
        success = storage.add_message(
            message_id=message_id,
            tree_hole_id=msg["tree_hole_id"],
            user_id=test_user_id,
            content=msg["content"],
            is_anonymous=True
        )
        if success:
            success_count += 1
            print(f"  ✓ [{msg['tree_hole_id']}] {msg['content'][:40]}...")
        else:
            print(f"  ✗ 消息添加失败")
    
    print(f"\n成功添加 {success_count}/{len(test_messages)} 条消息")
    
    # 验证数据
    print("\n3. 验证数据...")
    all_holes = storage.get_all_tree_holes_with_messages(hours=168)
    for hole in all_holes:
        print(f"  ✓ {hole['title']}: {hole['message_count']} 条消息")
    
    print("\n" + "=" * 60)
    print("✅ 测试数据初始化完成！")
    print("=" * 60)
    print("\n提示：")
    print("  - 访问 http://localhost:5001/api/tree-hole/tree-holes 查看树洞列表")
    print("  - 访问 http://localhost:5001/api/tree-hole/trending-decisions 查看热门决策")
    print("\n")
    
    storage.close()


if __name__ == "__main__":
    try:
        init_test_data()
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
