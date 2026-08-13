"""
core — 核心业务逻辑

包含系统提示词、LLM 客户端封装和 ReAct Agent 主循环。
"""

from core.prompt import AGENT_SYSTEM_PROMPT
from core.client import OpenAICompatibleClient
from core.agent import TravelAssistant, _extract_action, _parse_action, _run_tool_cycle, llm

__all__ = [
    "AGENT_SYSTEM_PROMPT",
    "OpenAICompatibleClient",
    "TravelAssistant",
    "_extract_action",
    "_parse_action",
    "_run_tool_cycle",
    "llm",
]