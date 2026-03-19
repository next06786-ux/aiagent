#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""自动修复所有语法错误"""

import ast
import re

def fix_syntax_errors():
    max_iterations = 50  # 最多修复50次
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        print(f"\n=== 第 {iteration} 次检查 ===")
        
        try:
            with open('backend/main.py', 'r', encoding='utf-8') as f:
                code = f.read()
            
            # 尝试解析
            ast.parse(code)
            print("✓ 语法检查通过!")
            return True
            
        except SyntaxError as e:
            print(f"发现错误: 行 {e.lineno}, {e.msg}")
            
            # 读取文件
            with open('backend/main.py', 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if e.lineno and e.lineno <= len(lines):
                error_line_idx = e.lineno - 1
                error_line = lines[error_line_idx]
                
                print(f"错误行: {error_line.rstrip()}")
                
                # 根据错误类型进行修复
                if 'unexpected indent' in e.msg:
                    # 缩进错误 - 检查上一行
                    if error_line_idx > 0:
                        prev_line = lines[error_line_idx - 1]
                        
                        # 如果上一行是注释
                        if prev_line.strip().startswith('#'):
                            # 检查注释末尾是否缺字
                            comment_endings = {
                                '数': '据', '过': '程', '分': '析', '处': '理',
                                '信': '息', '消': '息', '状': '态', '内': '容',
                                '进': '度', '获': '取', '格': '式', '模': '式',
                                '时': ')', '式': ')', '化': ')', '态': ')',
                            }
                            
                            fixed = False
                            for incomplete, complete in comment_endings.items():
                                if prev_line.rstrip().endswith(incomplete):
                                    lines[error_line_idx - 1] = prev_line.rstrip() + complete + '\n'
                                    print(f"  修复: 补全注释 '{incomplete}{complete}'")
                                    fixed = True
                                    break
                            
                            if not fixed:
                                # 添加换行
                                if not prev_line.endswith('\n'):
                                    lines[error_line_idx - 1] = prev_line + '\n'
                                    print(f"  修复: 添加换行")
                
                elif 'unterminated string' in e.msg:
                    # 未闭合的字符串
                    if '"' in error_line and error_line.count('"') % 2 != 0:
                        # 在行尾添加引号
                        lines[error_line_idx] = error_line.rstrip() + '"\n'
                        print(f"  修复: 添加闭合引号")
                
                # 写回文件
                with open('backend/main.py', 'w', encoding='utf-8') as f:
                    f.writelines(lines)
            else:
                print(f"  无法定位错误行")
                break
        
        except Exception as e:
            print(f"其他错误: {e}")
            break
    
    print(f"\n已完成 {iteration} 次修复尝试")
    return False

if __name__ == '__main__':
    import sys
    import io
    # 设置输出编码为UTF-8
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    success = fix_syntax_errors()
    if success:
        print("\n✓ 所有语法错误已修复!")
    else:
        print("\n警告: 仍有错误需要手动修复")
