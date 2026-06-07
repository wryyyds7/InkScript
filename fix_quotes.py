#!/usr/bin/env python3
"""修复 window.py 中的中文引号问题"""

import sys
from pathlib import Path

def fix_chinese_quotes(file_path):
    """修复文件中的中文引号"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换中文引号
        modified = False
        if '”' in content:
            content = content.replace('”', '"')
            modified = True
            print(f"✅ 已修复中文引号：{file_path}")
        
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 文件已保存：{file_path}")
        else:
            print(f"ℹ️ 文件中未找到中文引号：{file_path}")
        
        return True
    except Exception as e:
        print(f"❌ 修复失败：{e}")
        return False

if __name__ == '__main__':
    file_path = Path(__file__).parent / 'novel2script' / 'desktop' / 'window.py'
    if fix_chinese_quotes(file_path):
        print("✅ 修复完成")
    else:
        print("❌ 修复失败")
        sys.exit(1)
