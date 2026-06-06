import os

# 创建 4 个内置 Skill 目录
skill_names = [
    'character-analysis',
    'dialogue-polish', 
    'style-adapt',
    'chapter-summary'
]

base_dir = 'novel2script/skills/builtins'

for skill_name in skill_names:
    skill_dir = os.path.join(base_dir, skill_name)
    os.makedirs(skill_dir, exist_ok=True)
    print(f'Created directory: {skill_dir}')

print('All skill directories created successfully!')
