import os
from tavily import TavilyClient


def get_hotel(city: str, budget_level: str = "mid-range") -> str:
    """推荐当地酒店和住宿"""
    api_key = os.getenv("TAVILY_API_KEY")
    tavily_client = TavilyClient(api_key=api_key)

    level_map = {
        "budget": "经济型酒店 青旅",
        "mid-range": "舒适型酒店 商务酒店",
        "luxury": "高端酒店 豪华度假酒店",
    }
    desc = level_map.get(budget_level, "舒适型酒店")
    query = f"{city} {desc} 住宿推荐 民宿"

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
            return "抱歉，没有找到相关的住宿推荐。"
        return "根据搜索，为您找到以下住宿信息：\n" + "\n".join(formatted_results)

    except Exception as e:
        return f"错误：查询住宿信息时出现问题-{e}"