import os
from tavily import TavilyClient


def get_transport(city: str) -> str:
    """查询城市交通指南（机场、火车站、地铁、打车等）"""
    api_key = os.getenv("TAVILY_API_KEY")
    tavily_client = TavilyClient(api_key=api_key)
    query = f"{city}交通指南 机场 火车站 地铁 出租车 网约车"

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
            return "抱歉，没有找到相关的交通信息。"
        return "根据搜索，为您找到以下交通信息：\n" + "\n".join(formatted_results)

    except Exception as e:
        return f"错误：查询交通信息时出现问题-{e}"
