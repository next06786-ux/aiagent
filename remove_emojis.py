#!/usr/bin/env python3
"""移除 decision_personas.py 中的所有 emoji 表情"""

import re

# 读取文件
with open('backend/decision/decision_personas.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 定义 emoji 替换规则
emoji_replacements = {
    '🎭': '',
    '🚀': '',
    '⏱️': '',
    '✅': '',
    '❌': '',
    '📋': '',
    '👀': '',
    '🤔': '',
    '⚖️': '',
    '📝': '',
    '🔄': '',
    '🧠': '',
    '⏳': '',
    '🌅': '',
}

# 批量替换
for emoji, replacement in emoji_replacements.items():
    content = content.replace(emoji, replacement)

# 清理多余的空格
content = re.sub(r'  +', ' ', content)  # 多个空格替换为一个
content = re.sub(r'\[ +', '[', content)  # [  替换为 [
content = re.sub(r' +\]', ']', content)  # 空格] 替换为 ]

# 写回文件
with open('backend/decision/decision_personas.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("已移除所有 emoji 表情")
