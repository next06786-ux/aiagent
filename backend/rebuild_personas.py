#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
重建decision_personas.py文件
从原始参考文件逐段读取并用正确的UTF-8编码重写
"""
import re

def rebuild_file():
    """重建文件"""
    print("开始重建 decision_personas.py...")
    
    # 读取原始参考文件
    with open('backend/decision/decision_personas_original_reference.txt', 'rb') as f:
        raw_content = f.read()
    
    # 尝试用UTF-8解码，忽略错误
    content = raw_content.decode('utf-8', errors='ignore')
    
    print(f"原文件: {len(content)} 字符, {len(content.splitlines())} 行")
    
    # 清理内容：移除不可打印字符（保留换行、制表符等）
    cleaned_lines = []
    for line in content.splitlines():
        # 保留代码行，清理乱码注释
        cleaned_line = ''.join(
            char if char.isprintable() or char in '\n\r\t' else ''
            for char in line
        )
        cleaned_lines.append(cleaned_line)
    
    cleaned_content = '\n'.join(cleaned_lines)
    
    # 写入新文件
    output_file = 'backend/decision/decision_personas_rebuilt.py'
    with open(output_file, 'w', encoding='utf-8', newline='\n') as f:
        f.write(cleaned_content)
    
    print(f"✅ 重建完成: {output_file}")
    print(f"   新文件: {len(cleaned_content)} 字符, {len(cleaned_lines)} 行")
    
    # 验证语法
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            compile(f.read(), output_file, 'exec')
        print("✅ Python 语法检查通过")
        return True
    except SyntaxError as e:
        print(f"❌ 语法错误: {e}")
        print(f"   行号: {e.lineno}, 位置: {e.offset}")
        return False

if __name__ == "__main__":
    if rebuild_file():
        print("\n✅ 重建成功！")
        print("下一步: 检查 decision_personas_rebuilt.py 并替换原文件")
    else:
        print("\n❌ 重建失败，需要手动修复")
