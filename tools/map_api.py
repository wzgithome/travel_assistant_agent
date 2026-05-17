import requests
from config.settings import GAODE_API_KEY


def show_map(city: str, attractions: str) -> str:
    """查询景点的地理位置信息（高德地图地理编码）"""
    api_key = GAODE_API_KEY
    if not api_key:
        return "错误：未配置 GAODE_API_KEY，无法使用地图功能。请在 .env 文件中添加 GAODE_API_KEY。"

    attraction_list = [a.strip() for a in attractions.split(",") if a.strip()]
    if not attraction_list:
        return "错误：未提供有效的景点名称。"

    results = []
    for name in attraction_list:
        try:
            resp = requests.get(
                "https://restapi.amap.com/v3/geocode/geo",
                params={"address": name, "city": city, "key": api_key},
                timeout=10,
            )
            data = resp.json()
            if data.get("status") == "1" and data.get("geocodes"):
                geo = data["geocodes"][0]
                formatted_address = geo.get("formatted_address", "未知")
                district = geo.get("district", "")
                location = geo.get("location", "")
                results.append(f"- {name}：位于{district}{formatted_address}（坐标：{location}）")
            else:
                results.append(f"- {name}：未找到位置信息")
        except Exception as e:
            results.append(f"- {name}：查询失败（{e}）")

    return f"📍 {city}景点位置信息：\n" + "\n".join(results)


def get_route(city: str, origin: str, destination: str, mode: str = "walk") -> str:
    """查询两个景点之间的路线（高德地图路径规划）"""
    api_key = GAODE_API_KEY
    if not api_key:
        return "错误：未配置 GAODE_API_KEY，无法使用路线功能。请在 .env 文件中添加 GAODE_API_KEY。"

    def geocode(place):
        resp = requests.get(
            "https://restapi.amap.com/v3/geocode/geo",
            params={"address": place, "city": city, "key": api_key},
            timeout=10,
        )
        data = resp.json()
        if data.get("status") == "1" and data.get("geocodes"):
            return data["geocodes"][0]["location"]
        return None

    origin_loc = geocode(origin)
    dest_loc = geocode(destination)
    if not origin_loc:
        return f"错误：无法定位出发地「{origin}」"
    if not dest_loc:
        return f"错误：无法定位目的地「{destination}」"

    mode_map = {
        "walk": ("walking", "步行"),
        "drive": ("driving", "驾车"),
        "bus": ("transit/integrated", "公交"),
    }
    api_type, mode_name = mode_map.get(mode, ("walking", "步行"))

    try:
        url = f"https://restapi.amap.com/v3/direction/{api_type}"
        params = {
            "origin": origin_loc,
            "destination": dest_loc,
            "key": api_key,
        }
        if mode == "drive":
            params["strategy"] = 0
        if mode == "bus":
            params["city1"] = city
            params["city2"] = city
            params["strategy"] = 0

        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()

        if data.get("status") != "1":
            return f"错误：路径规划失败 - {data.get('info', '未知错误')}"

        if mode == "walk":
            route = data.get("route", {})
            paths = route.get("paths", [])
            if not paths:
                return f"未找到从{origin}到{destination}的{mode_name}路线"
            paths.sort(key=lambda p: int(p.get("duration", 0)))
            path = paths[0]
            distance = int(path.get("distance", 0))
            duration = int(path.get("duration", 0))
            steps = path.get("steps", [])
            steps_text = []
            for i, step in enumerate(steps[:8], 1):
                instruction = step.get("instruction", "")
                steps_text.append(f"  {i}. {instruction}")
            return (f"🚶 {origin} → {destination}（时间最短步行路线）\n"
                    f"距离：{distance}米，约{duration // 60}分钟\n"
                    f"路线：\n" + "\n".join(steps_text))

        elif mode == "drive":
            route = data.get("route", {})
            paths = route.get("paths", [])
            if not paths:
                return f"未找到从{origin}到{destination}的{mode_name}路线"
            paths.sort(key=lambda p: int(p.get("duration", 0)))
            path = paths[0]
            distance = int(path.get("distance", 0))
            duration = int(path.get("duration", 0))
            steps = path.get("steps", [])
            steps_text = []
            for i, step in enumerate(steps[:8], 1):
                instruction = step.get("instruction", "")
                steps_text.append(f"  {i}. {instruction}")
            return (f"🚗 {origin} → {destination}（时间最短驾车路线）\n"
                    f"距离：{distance / 1000:.1f}公里，约{duration // 60}分钟\n"
                    f"路线：\n" + "\n".join(steps_text))

        elif mode == "bus":
            transits = data.get("route", {}).get("transits", [])
            if not transits:
                return f"未找到从{origin}到{destination}的公交路线"

            def extract_transit_info(transit):
                segments = transit.get("segments", [])
                lines = []
                has_subway = False
                for seg in segments:
                    railway = seg.get("railway", {})
                    if railway and railway.get("name"):
                        lines.append(railway["name"])
                        has_subway = True
                    bus = seg.get("bus", {})
                    if bus and bus.get("buslines"):
                        line_name = bus["buslines"][0].get("name", "")
                        if line_name:
                            lines.append(line_name)
                return lines, has_subway

            scored = []
            for t in transits:
                dur = int(t.get("duration", 0))
                lines, has_subway = extract_transit_info(t)
                score = dur * (0.8 if has_subway else 1.0)
                scored.append((score, dur, lines, has_subway, t))

            scored.sort(key=lambda x: x[0])
            _, duration, lines, has_subway, transit = scored[0]

            lines_text = " → ".join(lines) if lines else "步行"
            tag = "地铁优先·时间最短" if has_subway else "时间最短公交路线"
            icon = "🚇" if has_subway else "🚌"
            return (f"{icon} {origin} → {destination}（{tag}）\n"
                    f"约{duration // 60}分钟，乘坐：{lines_text}")

    except Exception as e:
        return f"错误：路径规划请求失败-{e}"
