import os
from tavily import TavilyClient


def get_attraction(city: str, weather: str) -> str:
    """根据城市和天气搜索推荐的旅游景点"""
    api_key = os.getenv("TAVILY_API_KEY")
    tavily_client = TavilyClient(api_key=api_key)
    query = f"'{city}' 在'{weather}'天气下最值得去的旅游景点推荐及理由"

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
            return "抱歉，没有找到相关的旅游景点推荐。"
        return "根据搜索，为您找到以下信息：\n" + "\n".join(formatted_results)

    except Exception as e:
        return f"错误：执行 Tavily 搜索时出现问题-{e}"
