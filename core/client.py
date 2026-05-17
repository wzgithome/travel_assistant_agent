from openai import OpenAI


class OpenAICompatibleClient:
    """一个用于调用任何兼容 OpenAI 接口的 LLM 服务的客户端。"""

    def __init__(self, model: str, api_key: str, base_url: str):
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate(self, messages: list[dict]) -> str:
        """调用 LLM API 来生成回应，接收完整的 messages 列表（含 system 消息）。"""
        print("正在调用大语言模型")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False
            )
            answer = response.choices[0].message.content
            print("大语言模型响应成功。")
            return answer
        except Exception as e:
            print(f"调用 LLM API 时发生错误：{e}")
            return "错误：调用语言模型服务时出错。"

    def generate_stream(self, messages: list[dict]):
        """流式调用 LLM API，逐 chunk yield 文本片段。"""
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"错误：调用语言模型服务时出错。{e}"
