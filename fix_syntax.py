#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复 projects.py 中的语法错误"""

file_path = r'd:\bianchenglianxi\project\InkScript\novel2script\api\routes\v1\projects.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 修复第669行（索引668）
if ': 0,' in lines[668] and '"data"' in lines[668]:
    lines[668] = '        return {"code": 0, "data": []}\n'

# 修复第682行（索引681）
if ': 0,' in lines[681] and '"data"' in lines[681]:
    lines[681] = '    return {"code": 0, "data": files}\n'

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Syntax errors fixed successfully')
