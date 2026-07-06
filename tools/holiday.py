import requests
from datetime import datetime


# ── 本地兜底数据（2026 年法定节假日） ──────────────────────────
_HOLIDAYS_2026 = {
    "元旦": {"start": "2026-01-01", "end": "2026-01-03", "days_off": 3},
    "春节": {"start": "2026-02-17", "end": "2026-02-23", "days_off": 7},
    "清明节": {"start": "2026-04-04", "end": "2026-04-06", "days_off": 3},
    "劳动节": {"start": "2026-05-01", "end": "2026-05-05", "days_off": 5},
    "端午节": {"start": "2026-06-19", "end": "2026-06-21", "days_off": 3},
    "中秋节": {"start": "2026-09-27", "end": "2026-09-29", "days_off": 3},
    "国庆节": {"start": "2026-10-01", "end": "2026-10-07", "days_off": 7},
}

_HOLIDAYS_FALLBACK = {2026: _HOLIDAYS_2026}

# ── 缓存 ──────────────────────────────────────────────────────
_cache: dict[int, dict] = {}

_API_BASE = "http://timor.tech/api/holiday/year"


def _fetch_holidays_from_api(year: int) -> dict | None:
    """
    从 timor.tech API 获取指定年份的节假日数据。
    返回格式与本地兜底数据一致的字典，失败返回 None。
    """
    try:
        resp = requests.get(f"{_API_BASE}/{year}", timeout=5)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return None

    if data.get("code") != 0 or "holiday" not in data:
        return None

    # API 返回的是按日期索引的字典，需要聚合为按假期名分组
    # 格式示例: "2026-01-01": {"holiday": true, "name": "元旦", "wage": 3, "date": "2026-01-01"}
    holiday_dates: dict[str, dict] = data["holiday"]
    groups: dict[str, list[str]] = {}

    for date_str, info in holiday_dates.items():
        if not info.get("holiday"):
            continue
        name = info.get("name", "未知")
        groups.setdefault(name, []).append(date_str)

    if not groups:
        return None

    result = {}
    for name, dates in groups.items():
        dates.sort()
        result[name] = {
            "start": dates[0],
            "end": dates[-1],
            "days_off": len(dates),
        }
    return result


def _get_holidays(year: int) -> dict:
    """获取节假日数据，优先 API，失败回退本地硬编码。"""
    if year in _cache:
        return _cache[year]

    api_data = _fetch_holidays_from_api(year)
    if api_data:
        _cache[year] = api_data
        return api_data

    fallback = _HOLIDAYS_FALLBACK.get(year)
    if fallback:
        return fallback

    return {}


def _find_holiday_for_date(target, holidays: dict) -> tuple[str, dict] | None:
    """在节假日字典中查找目标日期所属的假期，返回 (名称, 信息) 或 None。"""
    for name, info in holidays.items():
        start = datetime.strptime(info["start"], "%Y-%m-%d").date()
        end = datetime.strptime(info["end"], "%Y-%m-%d").date()
        if start <= target <= end:
            return name, info
    return None


def check_holiday(date_str: str = "") -> str:
    """
    查询指定日期是否为节假日，或列出即将到来的节假日。
    用于行程规划时判断是否为旅游高峰期。

    Args:
        date_str: 日期，格式 YYYY-MM-DD。为空时列出所有节假日信息。
    """
    today = datetime.now().date()

    if not date_str:
        # 列出当前年的所有节假日
        holidays = _get_holidays(today.year)
        if not holidays:
            return f"🗓️ 暂未获取到 {today.year} 年的节假日数据，请稍后再试。"

        lines = [f"🗓️ {today.year}年中国法定节假日:"]
        for name, info in holidays.items():
            start = datetime.strptime(info["start"], "%Y-%m-%d").date()
            end = datetime.strptime(info["end"], "%Y-%m-%d").date()
            status = "✅ 已过" if end < today else "🔴 进行中" if start <= today <= end else "⏳ 未到"
            lines.append(f"  {name}: {info['start']} ~ {info['end']}（{info['days_off']}天）{status}")
        lines.append("\n💡 提示: 节假日期间景点人流量大、住宿价格上涨，建议提前预订或避开高峰。")
        return "\n".join(lines)

    # 解析指定日期
    try:
        target = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return "错误：日期格式不正确，请使用 YYYY-MM-DD 格式，如 2026-05-01"

    holidays = _get_holidays(target.year)
    if holidays:
        found = _find_holiday_for_date(target, holidays)
        if found:
            name, info = found
            return (f"🗓️ {date_str} 是 {name} 假期（{info['start']}~{info['end']}，共{info['days_off']}天）\n"
                    f"⚠️ 节假日期间：景点人流量大、住宿价格可能上涨2~3倍，建议提前预订门票和酒店。")

    # 检查是否为周末
    weekday = target.weekday()
    if weekday >= 5:
        return f"🗓️ {date_str} 是周末（{'周六' if weekday == 5 else '周日'}），非法定节假日，但部分热门景点人可能较多。"

    return f"🗓️ {date_str} 是普通工作日，非节假日，适合出行（景点人少、住宿价格较低）。"