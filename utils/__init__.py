"""
utils — 通用工具函数

提供 token 截断等辅助功能。
"""

from utils.tokenizer import _truncate_observation, MAX_OBSERVATION_LENGTH

__all__ = [
    "_truncate_observation",
    "MAX_OBSERVATION_LENGTH",
]