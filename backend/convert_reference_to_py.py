#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将decision_personas_original_reference.txt转换为decision_personas.py
确保没有编码问题
"""

def convert_reference_to_py():
    """转换参考文件为Python文件"""
    
    input_file = "backend/decision/decision_personas_original_reference.txt"
    output_file = "backend/decision/decision_personas.py"
    backup_file = "backend/decision/decision_personas_backup.py"
    
    print(f"开始转换...")
    print(f"输入文件: {input_file}")
    print(f"输出文件: {output_file}")
    
    try:
        # 备份当前文件
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                current_content = f.read()
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(current_content)
            print(f"✓ 已备份当前文件到: {backup_file}")
        except FileNotFoundError:
            print("当前文件不存在，跳过备份")
        
        # 尝试多种编码读取参考文件
        content = None
        encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                print(f"尝试使用 {encoding} 编码读取...")
                with open(input_file, 'r', encoding=encoding) as f:
                    content = f.read()
                print(f"✓ 成功使用 {encoding} 编码读取")
                break
            except (UnicodeDecodeError, LookupError) as e:
                print(f"  {encoding} 失败: {e}")
                continue
        
        if content is None:
            raise Exception("无法使用任何已知编码读取文件")
        
        print(f"✓ 读取参考文件成功，共 {len(content)} 字符")
        
        # 检查是否有问号（编码问题的标志）
        question_mark_count = content.count('?')
        print(f"  检测到 {question_mark_count} 个问号字符")
        
        # 直接写入（保持UTF-8编码）
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ 转换完成！")
        print(f"✓ 新文件已保存到: {output_file}")
        
        # 验证写入
        with open(output_file, 'r', encoding='utf-8') as f:
            verify_content = f.read()
        
        if len(verify_content) == len(content):
            print(f"✓ 验证成功：文件大小匹配 ({len(verify_content)} 字符)")
        else:
            print(f"⚠ 警告：文件大小不匹配")
            print(f"  原始: {len(content)} 字符")
            print(f"  写入: {len(verify_content)} 字符")
        
        # 检查Python语法
        try:
            compile(verify_content, output_file, 'exec')
            print(f"✓ Python语法检查通过")
        except SyntaxError as e:
            print(f"⚠ 语法错误: {e}")
            print(f"  行号: {e.lineno}")
            print(f"  位置: {e.offset}")
        
        return True
        
    except Exception as e:
        print(f"✗ 转换失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = convert_reference_to_py()
    if success:
        print("\n" + "="*60)
        print("转换成功！")
        print("="*60)
        print("\n下一步:")
        print("1. 检查 backend/decision/decision_personas.py")
        print("2. 如果有问题，可以从 backend/decision/decision_personas_backup.py 恢复")
        print("3. 重启后端服务测试")
    else:
        print("\n" + "="*60)
        print("转换失败，请检查错误信息")
        print("="*60)
