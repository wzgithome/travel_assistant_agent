import requests


def get_weather(city: str) -> str:
    """通过调用 wttr.in API 查询真实的天气信息"""
    url = f"https://wttr.in/{city}?format=j1"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        current = data['current_condition'][0]
        humidity = current['humidity']
        wind_speed = current['windSpeedKmph']
        current_condition = data['current_condition'][0]
        weather_desc = current_condition['weatherDesc'][0]['value']
        temp_c = current_condition['temp_C']
        return (f"🌤️ {city}今日天气:\n"
                f"- 状况:{weather_desc}\n"
                f"- 气温:{temp_c}°C (体感{current['FeelsLikeC']}°C)\n"
                f"- 湿度:{humidity}%\n"
                f"- 风速:{wind_speed}km/h\n\n"
                f"💡 建议: {'适合户外活动' if weather_desc not in ['雨', '阴'] else '记得带伞~'}")
    except requests.exceptions.RequestException as e:
        return f"错误：查询天气时遇到网络问题-{e}"
    except (KeyError, IndexError) as e:
        return f"错误：解析天气数据失败，可能是城市名称无效 - {e}"


def get_weather_forecast(city: str, days: int = 3) -> str:
    """查询城市未来几天的天气预报，用于行程规划"""
    url = f"https://wttr.in/{city}?format=j1"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        forecasts = data.get("weather", [])[:days]
        if not forecasts:
            return f"错误：未获取到{city}的天气预报数据"

        lines = [f"📅 {city}未来{len(forecasts)}天天气预报:"]
        for day in forecasts:
            date = day["date"]
            max_temp = day["maxtempC"]
            min_temp = day["mintempC"]
            # 取白天天气描述
            hourly = day.get("hourly", [{}])
            desc = hourly[len(hourly) // 2].get("weatherDesc", [{}])[0].get("value", "未知") if hourly else "未知"
            rain_chance = hourly[len(hourly) // 2].get("chanceofrain", "0") if hourly else "0"

            lines.append(f"  {date}: {desc}, {min_temp}~{max_temp}°C, 降雨概率{rain_chance}%")

        return "\n".join(lines)

    except requests.exceptions.RequestException as e:
        return f"错误：查询天气预报时遇到网络问题-{e}"
    except (KeyError, IndexError) as e:
        return f"错误：解析天气预报数据失败 - {e}"
