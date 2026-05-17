import os
from tavily import TavilyClient


def get_restaurant(city: str, cuisine_type: str = "all") -> str:
    """推荐当地特色美食和餐厅"""
    api_key = os.getenv("TAVILY_API_KEY")
    tavily_client = TavilyClient(api_key=api_key)

    type_map = {
        "all": "全品类美食推荐",
        "local": "本地特色小吃",
        "famous": "知名餐厅推荐",
        "budget": "经济实惠美食",
        "high-end": "高端餐饮推荐",
    }
    desc = type_map.get(cuisine_type, "全品类美食推荐")
    query = f"{city} {desc} 特色美食 餐厅推荐"

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
            return "抱歉，没有找到相关的美食推荐。"
        return "根据搜索，为您找到以下美食信息：\n" + "\n".join(formatted_results)

    except Exception as e:
        return f"错误：查询美食信息时出现问题-{e}"
