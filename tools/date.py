from datetime import datetime


def get_current_date() -> str:
    """获取当前日期和星期信息"""
    now = datetime.now()
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    weekday = weekdays[now.weekday()]
    return f"当前日期：{now.strftime('%Y年%m月%d日')} {weekday}"
