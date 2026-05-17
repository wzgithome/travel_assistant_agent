import os
from tavily import TavilyClient


def estimate_budget(city: str, days: int = 3, travel_style: str = "mid-range") -> str:
    """估算旅行预算"""
    api_key = os.getenv("TAVILY_API_KEY")
    tavily_client = TavilyClient(api_key=api_key)

    style_map = {
        "budget": "经济型穷游",
        "mid-range": "舒适型",
        "luxury": "豪华型",
    }
    style_desc = style_map.get(travel_style, "舒适型")
    query = f"{city}{days}天{style_desc}旅行预算 住宿餐饮交通门票费用"

    try:
        response = tavily_client.search(
            query=query,
            search_depth="basic",
            include_answer=True
        )
        if response.get("answer"):
            return response["answer"]

        formatted_results = []
        for result in response.get("results", []):
            formatted_results.append(f"- {result['title']}:{result['content']}")

        if not formatted_results:
            return "抱歉，没有找到相关的预算信息。"
        return "根据搜索，为您找到以下预算参考：\n" + "\n".join(formatted_results)

    except Exception as e:
        return f"错误：查询预算信息时出现问题-{e}"
