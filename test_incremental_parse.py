#!/usr/bin/env python3
"""测试增量JSON解析"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from backend.decision.lora_decision_analyzer import LoRADecisionAnalyzer

# 模拟流式生成的JSON数据
test_chunks = [
    '{"month": 1, "event": "开始新工作", "impact": {"career": 0.3}, "probability": 0.8}',
    '{"month": 2, "event": "适应期挑战", "impact": {"stress": 0.2}, "probability": 0.7}',
    '{"month": 3, "event": "获得认可", "impact": {"career": 0.4, "confidence": 0.3}, "probability": 0.6}',
]

# 模拟累积的buffer
buffer = ""
emitted_months = []

analyzer = LoRADecisionAnalyzer()

print("=" * 60)
print("测试增量JSON解析")
print("=" * 60)

for i, chunk in enumerate(test_chunks):
    buffer += chunk + "\n"
    print(f"\n--- 第 {i+1} 次解析 (buffer长度: {len(buffer)}) ---")
    print(f"已发送月份: {emitted_months}")
    
    events = analyzer.extract_incremental_events(buffer, emitted_months)
    
    print(f"解析出 {len(events)} 个新事件:")
    for event in events:
        print(f"  M{event['month']}: {event['event']}")

print("\n" + "=" * 60)
print(f"最终: 共发送 {len(emitted_months)} 个月份的事件")
print("=" * 60)
