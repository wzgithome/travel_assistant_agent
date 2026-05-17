from datetime import datetime, timedelta


# 2026年中国法定节假日（含调休放假日期范围）
HOLIDAYS_2026 = {
    "元旦": {"start": "2026-01-01", "end": "2026-01-03", "days_off": 3},
    "春节": {"start": "2026-02-17", "end": "2026-02-23", "days_off": 7},
    "清明节": {"start": "2026-04-04", "end": "2026-04-06", "days_off": 3},
    "劳动节": {"start": "2026-05-01", "end": "2026-05-05", "days_off": 5},
    "端午节": {"start": "2026-06-19", "end": "2026-06-21", "days_off": 3},
    "中秋节": {"start": "2026-09-27", "end": "2026-09-29", "days_off": 3},
    "国庆节": {"start": "2026-10-01", "end": "2026-10-07", "days_off": 7},
}


def check_holiday(date_str: str = "") -> str:
    """
    查询指定日期是否为节假日，或列出即将到来的节假日。
    用于行程规划时判断是否为旅游高峰期。

    Args:
        date_str: 日期，格式 YYYY-MM-DD。为空时列出所有节假日信息。
    """
    if not date_str:
        lines = ["🗓️ 2026年中国法定节假日:"]
        today = datetime.now().date()
        for name, info in HOLIDAYS_2026.items():
            start = datetime.strptime(info["start"], "%Y-%m-%d").date()
            end = datetime.strptime(info["end"], "%Y-%m-%d").date()
            status = "✅ 已过" if end < today else "🔴 进行中" if start <= today <= end else "⏳ 未到"
            lines.append(f"  {name}: {info['start']} ~ {info['end']}（{info['days_off']}天）{status}")
        lines.append("\n💡 提示: 节假日期间景点人流量大、住宿价格上涨，建议提前预订或避开高峰。")
        return "\n".join(lines)

    try:
        target = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return f"错误：日期格式不正确，请使用 YYYY-MM-DD 格式，如 2026-05-01"

    for name, info in HOLIDAYS_2026.items():
        start = datetime.strptime(info["start"], "%Y-%m-%d").date()
        end = datetime.strptime(info["end"], "%Y-%m-%d").date()
        if start <= target <= end:
            return (f"🗓️ {date_str} 是 {name} 假期（{info['start']}~{info['end']}，共{info['days_off']}天）\n"
                    f"⚠️ 节假日期间：景点人流量大、住宿价格可能上涨2~3倍，建议提前预订门票和酒店。")

    # 检查是否为周末
    weekday = target.weekday()
    if weekday >= 5:
        return f"🗓️ {date_str} 是周末（{'周六' if weekday == 5 else '周日'}），非法定节假日，但部分热门景点人可能较多。"

    return f"🗓️ {date_str} 是普通工作日，非节假日，适合出行（景点人少、住宿价格较低）。"
