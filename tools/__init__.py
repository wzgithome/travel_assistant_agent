"""
tools — 外部工具集

封装天气、景点、美食、住宿、交通、地图等 API 调用，
供 Agent 在 ReAct 循环中按需调用。
"""

from tools.registry import available_tools
from tools.date import get_current_date
from tools.weather import get_weather, get_weather_forecast
from tools.holiday import check_holiday
from tools.attraction import get_attraction
from tools.transport import get_transport
from tools.restaurant import get_restaurant
from tools.hotel import get_hotel
from tools.budget import estimate_budget
from tools.map_api import show_map, get_route

__all__ = [
    "available_tools",
    "get_current_date",
    "get_weather",
    "get_weather_forecast",
    "check_holiday",
    "get_attraction",
    "get_transport",
    "get_restaurant",
    "get_hotel",
    "estimate_budget",
    "show_map",
    "get_route",
]