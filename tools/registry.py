from tools.weather import get_weather, get_weather_forecast
from tools.attraction import get_attraction
from tools.transport import get_transport
from tools.restaurant import get_restaurant
from tools.budget import estimate_budget
from tools.map_api import show_map, get_route
from tools.date import get_current_date
from tools.holiday import check_holiday

available_tools = {
    "get_weather": get_weather,
    "get_weather_forecast": get_weather_forecast,
    "get_attraction": get_attraction,
    "get_transport": get_transport,
    "get_restaurant": get_restaurant,
    "estimate_budget": estimate_budget,
    "show_map": show_map,
    "get_route": get_route,
    "get_current_date": get_current_date,
    "check_holiday": check_holiday,
}
