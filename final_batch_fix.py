#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""最终批量修复所有注释不完整的问题"""

import re

with open('backend/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 修复所有注释后紧跟代码的情况（缺少换行）
# 匹配模式: # xxx某字\n空格+代码
patterns = [
    (r'(#[^\n]*?)(数|过|分|处|信|消|状|内|进|获|格|模|训|加|检)\s*\n(\s+)(\w)', r'\1\2据\n\3\4'),  # 数据等
    (r'(#[^\n]*?过)\s*\n(\s+)(\w)', r'\1程\n\2\3'),
    (r'(#[^\n]*?分)\s*\n(\s+)(\w)', r'\1析\n\2\3'),
    (r'(#[^\n]*?处)\s*\n(\s+)(\w)', r'\1理\n\2\3'),
    (r'(#[^\n]*?信)\s*\n(\s+)(\w)', r'\1息\n\2\3'),
    (r'(#[^\n]*?消)\s*\n(\s+)(\w)', r'\1息\n\2\3'),
    (r'(#[^\n]*?状)\s*\n(\s+)(\w)', r'\1态\n\2\3'),
    (r'(#[^\n]*?内)\s*\n(\s+)(\w)', r'\1容\n\2\3'),
    (r'(#[^\n]*?进)\s*\n(\s+)(\w)', r'\1度\n\2\3'),
    (r'(#[^\n]*?获)\s*\n(\s+)(\w)', r'\1取\n\2\3'),
    (r'(#[^\n]*?格)\s*\n(\s+)(\w)', r'\1式\n\2\3'),
    (r'(#[^\n]*?模)\s*\n(\s+)(\w)', r'\1式\n\2\3'),
    (r'(#[^\n]*?训)\s*\n(\s+)(\w)', r'\1练\n\2\3'),
    (r'(#[^\n]*?加)\s*\n(\s+)(\w)', r'\1载\n\2\3'),
    (r'(#[^\n]*?检)\s*\n(\s+)(\w)', r'\1查\n\2\3'),
]

for pattern, replacement in patterns:
    content = re.sub(pattern, replacement, content)

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✓ 批量修复完成')
