#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查并报告所有语法错误"""

import ast
import sys

try:
    with open('backend/main.py', 'r', encoding='utf-8') as f:
        code = f.read()
    
    ast.parse(code)
    print('✓ 语法检查通过!')
    sys.exit(0)
    
except SyntaxError as e:
    print(f'✗ 语法错误:')
    print(f'  文件: {e.filename}')
    print(f'  行号: {e.lineno}')
    print(f'  位置: {e.offset}')
    print(f'  错误: {e.msg}')
    print(f'  代码: {e.text}')
    sys.exit(1)
