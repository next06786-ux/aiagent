"""
测试真实进度提示
验证AI处理过程中的进度回调是否正常工作
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from llm.deep_ai_processor import get_deep_ai_processor


def test_progress_callback():
    """测试进度回调"""
    print("=" * 60)
    print("测试真实进度提示")
    print("=" * 60)
    
    # 创建AI处理器
    user_id = "test_user"
    processor = get_deep_ai_processor(user_id)
    
    # 记录进度消息
    progress_messages = []
    
    def progress_callback(layer: int, message: str):
        """进度回调函数"""
        progress_text = f"第{layer}层：{message}"
        progress_messages.append(progress_text)
        print(f"📊 {progress_text}")
    
    # 测试消息
    test_message = "我最近睡眠不足，应该怎么办？"
    
    print(f"\n用户消息：{test_message}\n")
    
    # 处理消息
    result = processor.process(test_message, progress_callback=progress_callback)
    
    print("\n" + "=" * 60)
    print("进度消息汇总")
    print("=" * 60)
    for i, msg in enumerate(progress_messages, 1):
        print(f"{i}. {msg}")
    
    print("\n" + "=" * 60)
    print("处理结果")
    print("=" * 60)
    print(f"最终回复长度：{len(result['final_response'])} 字符")
    print(f"思考过程长度：{len(result['thinking_process'])} 字符")
    print(f"\n思考过程预览：")
    print(result['thinking_process'][:500] + "...")
    print(f"\n最终回复预览：")
    print(result['final_response'][:500] + "...")
    
    print("\n✅ 测试完成！")
    print(f"共收到 {len(progress_messages)} 条进度消息")


if __name__ == "__main__":
    test_progress_callback()
