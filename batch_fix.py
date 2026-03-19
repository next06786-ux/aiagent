#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""批量修复所有剩余问题"""

import re

with open('backend/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 修复所有未闭合的print语句
content = re.sub(r'print\(f"([^"]*?)信息\)(?!")', r'print(f"\1信息")', content)

# 修复注释
content = re.sub(r'# (.+?)效果\s*\n\s+(\w)', r'# \1效果)\n                \2', content)

# 修复数字
content = content.replace('推送0个字', '推送10个字')
content = content.replace('推送回复内 ', '推送回复内容 ')

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✓ 批量修复完成')
