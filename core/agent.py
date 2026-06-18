import os
import re
import json
from datetime import datetime

from core.prompt import AGENT_SYSTEM_PROMPT, SUPPORTED_CITIES
from core.client import OpenAICompatibleClient
from config.settings import API_KEY, BASE_URL, MODEL_ID
from tools.registry import available_tools
from utils.tokenizer import _truncate_observation


llm = OpenAICompatibleClient(
    model=MODEL_ID,
    api_key=API_KEY,
    base_url=BASE_URL,
)


class TravelAssistant:
    """旅行助手核心类，管理多轮对话状态（OpenAI messages 格式）"""

    HISTORY_FILE = "chat_history.json"

    def __init__(self):
        self.messages: list[dict] = []
        self.max_turns = 50
        self.context_messages_limit = 6

    def save(self):
        """将当前对话历史保存到 JSON 文件"""
        data = {
            "saved_at": datetime.now().isoformat(),
            "messages": self.messages,
        }
        with open(self.HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self) -> bool:
        """从 JSON 文件恢复对话历史，返回是否成功加载"""
        if not os.path.exists(self.HISTORY_FILE):
            return False
        try:
            with open(self.HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.messages = data.get("messages", [])
            saved_at = data.get("saved_at", "未知")
            print(f"📂 已恢复上次对话（保存于 {saved_at}），共 {len(self.messages)} 条消息\n")
            return True
        except (json.JSONDecodeError, KeyError) as e:
            print(f"⚠️ 对话历史文件损坏，将重新开始：{e}\n")
            return False

    def reset(self):
        """清空对话历史并删除存档文件"""
        self.messages = []
        if os.path.exists(self.HISTORY_FILE):
            os.remove(self.HISTORY_FILE)
        print("✅ 对话历史已清空\n")

    def add_message(self, role: str, content: str):
        """添加消息到历史记录，使用 OpenAI messages 格式"""
        if role == "user":
            self.messages.append({"role": "user", "content": content})
        else:
            self.messages.append({"role": "assistant", "content": content})

        if len(self.messages) > self.context_messages_limit:
            self._compress_old_messages()

    def _compress_old_messages(self):
        """压缩旧轮次的 assistant 消息，只保留最终答案，节省 Token"""
        last_user_idx = -1
        for i in range(len(self.messages) - 1, -1, -1):
            if self.messages[i]["role"] == "user":
                last_user_idx = i
                break

        for i in range(last_user_idx):
            msg = self.messages[i]
            if msg["role"] == "assistant":
                content = msg["content"]
                finish_match = re.search(r'Finish\[(.*?)]', content)
                if finish_match:
                    self.messages[i]["content"] = finish_match.group(1)
                elif len(content) > 300 and ("Thought:" in content or "Observation:" in content):
                    self.messages[i]["content"] = content[:200] + "...(已压缩)"

        if len(self.messages) > self.context_messages_limit:
            self.messages = self.messages[-self.context_messages_limit:]

    def get_context_summary(self, tool_call_count: int = 0) -> str:
        """获取对话上下文摘要（用于系统提示）"""
        base = f"当前支持的预设城市：{', '.join(SUPPORTED_CITIES)}"
        if tool_call_count >= 6:
            base += "\n【重要】你已经调用了足够的工具，收集了足够的信息。下一步必须用Finish[...]输出最终答案，禁止再调用任何工具！"
        elif tool_call_count >= 4:
            base += "\n【提示】你已经调用了多个工具，信息已基本充足。请考虑是否可以用Finish输出答案。"
        return base


def _extract_action(llm_output: str) -> tuple[str, bool]:
    """从模型输出中提取 Thought 和 Action"""
    match = re.search(
        r'(Thought:.*?Action:.*?)(?=\n\s*(?:Thought:|Action:|Observation:)|\Z)',
        llm_output,
        re.DOTALL
    )
    if match:
        return match.group(1).strip(), True
    return llm_output.strip(), False


def _parse_action(action_str: str):
    """解析 Action 字符串"""
    action_match = re.search(r'Action:\s*(.*)', action_str, re.DOTALL)
    if action_match:
        action_str = action_match.group(1).strip()

    if action_str.startswith("Finish"):
        match = re.match(r"Finish\[(.*)]", action_str)
        if match:
            return {"type": "finish", "content": match.group(1)}
        return {"type": "finish", "content": action_str[len("Finish"):].strip("[]() ")}

    tool_match = re.search(r'(\w+)\((.*)\)', action_str)
    if tool_match:
        tool_name = tool_match.group(1)
        args_str = tool_match.group(2)
        kwargs = dict(re.findall(r'(\w+)="([^"]*)"', args_str))
        return {"type": "tool", "name": tool_name, "kwargs": kwargs}

    return {"type": "invalid", "content": action_str}


def _run_tool_cycle(assistant: TravelAssistant, verbose: bool = True):
    """运行单个工具调用循环（ReAct 模式）"""
    tool_call_count = 0
    for i in range(assistant.max_turns):
        if verbose:
            print(f"\n--- 工具调用 #{i + 1} ---\n")

        context_prompt = f"\n\n【系统提示】{assistant.get_context_summary(tool_call_count)}"
        system_message = {"role": "system", "content": AGENT_SYSTEM_PROMPT + context_prompt}
        llm_messages = [system_message] + assistant.messages

        llm_output = llm.generate(llm_messages)

        output_text, is_complete = _extract_action(llm_output)
        if output_text != llm_output.strip():
            if verbose:
                print("已截断多余的 Thought-Action 对")
            print(f"模型输出:\n{output_text}\n")
        else:
            if verbose:
                print(f"模型输出:\n{llm_output}\n")
            output_text = llm_output

        assistant.messages.append({"role": "assistant", "content": output_text})
        action_data = _parse_action(output_text)

        if action_data["type"] == "finish":
            if verbose:
                print(f"✅ 任务完成，最终答案:\n{action_data['content']}\n")
            return action_data['content']

        elif action_data["type"] == "tool":
            tool_call_count += 1
            tool_name = action_data["name"]
            kwargs = action_data["kwargs"]

            if tool_name in available_tools:
                observation = available_tools[tool_name](**kwargs)
            else:
                observation = f"错误：未定义的工具 '{tool_name}'"

            observation = _truncate_observation(observation)
            observation_str = f"\nObservation: {observation}"
            if verbose:
                print(f"Observation: {observation}\n" + "=" * 40)
            assistant.messages[-1]["content"] += observation_str

        else:
            answer = action_data.get("content", output_text)
            if verbose:
                print(f"✅ 直接回答:\n{answer}\n")
            return answer

    final_answer = "抱歉，我还没有找到满意的答案。请换个方式再试试。"
    if verbose:
        print(f"⚠️ 达到最大工具调用次数，最终答案：{final_answer}\n")
    assistant.messages.append({"role": "assistant", "content": f"结果：{final_answer}"})
    return final_answer
