import sys
from pathlib import Path

file_path = Path('E:/ai/backend/main.py')
content = file_path.read_text(encoding='utf-8')

# 在最开始插入路径修复
new_content = """import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

""" + content

file_path.write_text(new_content, encoding='utf-8')
print('✅ 已添加路径修复到 main.py')










