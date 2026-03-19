"""
测试AI聊天进度流程
验证进度更新是否真实绑定到处理层
"""

import requests
import time
import json

BASE_URL = "http://192.168.1.192:8000"

def test_chat_progress():
    """测试聊天进度流程"""
    print("=" * 60)
    print("测试AI聊天进度流程")
    print("=" * 60)
    
    # 1. 启动聊天会话
    print("\n1. 启动聊天会话...")
    start_response = requests.post(
        f"{BASE_URL}/api/chat/start",
        json={
            "user_id": "test_user",
            "message": "我最近睡眠不好，怎么办？",
            "context": None
        },
        timeout=10
    )
    
    if start_response.status_code != 200:
        print(f"❌ 启动失败: {start_response.status_code}")
        print(f"响应: {start_response.text}")
        return
    
    result = start_response.json()
    print(f"✅ 启动成功")
    print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    # 提取session_id（可能在data字段中）
    session_id = result.get("session_id")
    if not session_id and "data" in result:
        session_id = result["data"].get("session_id")
    
    if not session_id:
        print("❌ 未获取到session_id")
        return
    
    print(f"✅ Session ID: {session_id}")
    
    # 2. 轮询进度
    print("\n2. 开始轮询进度...")
    poll_count = 0
    max_polls = 100  # 最多轮询100次
    last_progress = ""
    last_thinking_len = 0
    last_answer_len = 0
    progress_updates = []
    
    while poll_count < max_polls:
        poll_count += 1
        time.sleep(0.1)  # 100ms轮询间隔
        
        try:
            poll_response = requests.get(
                f"{BASE_URL}/api/chat/poll/{session_id}",
                timeout=5
            )
            
            if poll_response.status_code != 200:
                print(f"❌ 轮询失败: {poll_response.status_code}")
                break
            
            response_json = poll_response.json()
            
            # 提取data字段
            progress_data = response_json.get("data", response_json)
            
            # 检查进度更新
            current_progress = progress_data.get("progress", "")
            if current_progress and current_progress != last_progress:
                print(f"📊 [{poll_count}] 进度: {current_progress}")
                progress_updates.append({
                    "poll": poll_count,
                    "progress": current_progress,
                    "time": time.time()
                })
                last_progress = current_progress
            
            # 检查思考过程更新
            thinking = progress_data.get("thinking", "")
            if thinking and len(thinking) > last_thinking_len:
                print(f"💭 [{poll_count}] 思考过程更新: {len(thinking)} 字符")
                last_thinking_len = len(thinking)
            
            # 检查回复内容更新
            answer = progress_data.get("answer", "")
            if answer and len(answer) > last_answer_len:
                print(f"📝 [{poll_count}] 回复内容更新: {len(answer)} 字符")
                last_answer_len = len(answer)
            
            # 检查是否完成
            if progress_data.get("done"):
                print(f"\n✅ [{poll_count}] 处理完成!")
                print(f"\n最终思考过程 ({len(thinking)} 字符):")
                print("-" * 60)
                print(thinking[:500] if len(thinking) > 500 else thinking)
                if len(thinking) > 500:
                    print("...")
                print("-" * 60)
                print(f"\n最终回复 ({len(answer)} 字符):")
                print("-" * 60)
                print(answer[:500] if len(answer) > 500 else answer)
                if len(answer) > 500:
                    print("...")
                print("-" * 60)
                break
            
            # 检查错误
            if progress_data.get("error"):
                print(f"❌ [{poll_count}] 错误: {progress_data.get('error')}")
                break
                
        except Exception as e:
            print(f"❌ [{poll_count}] 轮询异常: {e}")
            break
    
    # 3. 分析进度更新
    print("\n" + "=" * 60)
    print("进度更新分析")
    print("=" * 60)
    print(f"总轮询次数: {poll_count}")
    print(f"进度更新次数: {len(progress_updates)}")
    
    if progress_updates:
        print("\n进度更新时间线:")
        for i, update in enumerate(progress_updates):
            print(f"  {i+1}. [轮询 {update['poll']}] {update['progress']}")
        
        # 检查是否有6层进度
        progress_texts = [u['progress'] for u in progress_updates]
        has_layer1 = any("第1层" in p for p in progress_texts)
        has_layer2 = any("第2层" in p for p in progress_texts)
        has_layer3 = any("第3层" in p for p in progress_texts)
        has_layer4 = any("第4层" in p for p in progress_texts)
        has_layer5 = any("第5层" in p for p in progress_texts)
        has_layer6 = any("第6层" in p for p in progress_texts)
        
        print(f"\n6层处理进度检测:")
        print(f"  第1层 (元智能体): {'✅' if has_layer1 else '❌'}")
        print(f"  第2层 (历史记忆): {'✅' if has_layer2 else '❌'}")
        print(f"  第3层 (领域分析): {'✅' if has_layer3 else '❌'}")
        print(f"  第4层 (知识图谱): {'✅' if has_layer4 else '❌'}")
        print(f"  第5层 (智能策略): {'✅' if has_layer5 else '❌'}")
        print(f"  第6层 (回复生成): {'✅' if has_layer6 else '❌'}")
        
        all_layers = has_layer1 and has_layer2 and has_layer3 and has_layer4 and has_layer5 and has_layer6
        if all_layers:
            print("\n✅ 所有6层进度都已正确显示!")
        else:
            print("\n⚠️ 部分层的进度未显示")
    else:
        print("\n❌ 未检测到任何进度更新")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_chat_progress()
