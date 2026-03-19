#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""修复所有4个引号的问题"""

with open('backend/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换所有4个引号为3个引号
content = content.replace('""""', '"""')

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✓ 修复了所有4引号问题')
