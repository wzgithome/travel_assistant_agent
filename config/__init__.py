"""
config — 项目配置模块

从 .env 加载 API 密钥、模型 ID 等运行时配置。
"""

from config.settings import API_KEY, BASE_URL, MODEL_ID, TAVILY_API_KEY, GAODE_API_KEY

__all__ = [
    "API_KEY",
    "BASE_URL",
    "MODEL_ID",
    "TAVILY_API_KEY",
    "GAODE_API_KEY",
]