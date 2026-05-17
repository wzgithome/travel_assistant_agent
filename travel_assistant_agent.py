"""
兼容层 — re-export 所有符号，确保 web/app.py 无需修改即可正常工作。
实际实现已拆分到 core/、tools/、utils/、config/ 模块中。
新代码请直接从各模块导入。
"""

from core.prompt import AGENT_SYSTEM_PROMPT, SUPPORTED_CITIES
from core.client import OpenAICompatibleClient
from core.agent import (
    TravelAssistant,
    _extract_action,
    _parse_action,
    _run_tool_cycle,
    llm,
)
from utils.tokenizer import _truncate_observation
from tools.registry import available_tools


def run_interactive():
    from main import run_interactive as _run
    _run()


def run_single_turn(user_prompt: str) -> list:
    from main import run_single_turn as _run
    return _run(user_prompt)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--single":
        user_prompt = "你好，请帮我查询一下今天北京的天气，然后根据天气推荐一个合适的旅游景点。"
        run_single_turn(user_prompt)
    else:
        run_interactive()
