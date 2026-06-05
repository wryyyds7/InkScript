# fix_skill.py - 修复 extensibility-design-spec.md 中的 requires_llm 问题
import re

path = r"D:\bianchenglianxi\project\InkScript\docs\extensibility-design-spec.md"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. 在 SkillManager 类中补充 execute() 方法定义（放在 resolve_dependencies 之前）
# 先找到 "class SkillManager:" 和第一个 async def 之间的位置
pattern = r"(class SkillManager:.*?)(\n    async def resolve_dependencies)"
flags = re.DOTALL
match = re.search(pattern, content)

if match:
    insert_pos = match.start(2)  # 在 resolve_dependencies 之前插入
    new_execute = '''    async def execute(self, name: str, data: dict, config: dict) -> dict:
        \"\"\"执行单个 Skill，根据 requires_llm 决定是否传递 llm_client\"\"\"
        meta = self._registry.get(name)
        if not meta:
            raise SkillNotFoundError(f"Skill '{name}' 未找到")

        # 处理 requires_llm 字段
        requires_llm = meta.get("requires_llm", True)
        if not requires_llm:
            # 不需要 LLM 的 Skill，从 config 中移除 llm_client
            config = {k: v for k, v in config.items() if k != "llm_client"}

        # 加载并调用 Skill
        module = self._load_module(name)
        return await module.run(data, config)

    async def execute_safe(self, name: str, data: dict, config: dict) -> SkillResult:
        \"\"\"安全执行 Skill，异常不会传播到调用者\"\"\"
        start = time.monotonic()
        try:
            result = await self.execute(name, data, config)
            return SkillResult(
                skill_name=name, success=True, data=result,
                duration_seconds=time.monotonic() - start
            )
        except Exception as e:
            logger.error(f"Skill '{name}' 执行失败: {e}", exc_info=True)
            return SkillResult(
                skill_name=name, success=False,
                error=str(e), duration_seconds=time.monotonic() - start
            )

'''
    content = content[:insert_pos] + new_execute + content[insert_pos:]
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("OK: SkillManager.execute() 和 execute_safe() 已补充")
else:
    print("FAIL: 未找到插入位置")

# 2. 在 skill.json 格式说明中补充 requires_llm 字段的含义
skill_json_pattern = r"(\"requires_llm\": false\\s*\\n)"
if re.search(skill_json_pattern, content):
    print("INFO: skill.json 中已包含 requires_llm 字段")
else:
    print("WARN: skill.json 示例中未找到 requires_llm 字段")
