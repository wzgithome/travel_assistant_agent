import sys
import os
import json
import re
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, Response, request, send_from_directory, session
from travel_assistant_agent import (
    AGENT_SYSTEM_PROMPT,
    SUPPORTED_CITIES,
    OpenAICompatibleClient,
    TravelAssistant,
    _extract_action,
    _parse_action,
    _truncate_observation,
    available_tools,
    llm,
)

app = Flask(__name__, static_folder="static")
app.secret_key = os.urandom(24)

# 每个用户会话独立的 assistant 实例，避免并发干扰
assistants: dict[str, TravelAssistant] = {}


def get_assistant() -> TravelAssistant:
    """获取当前会话的 assistant，不存在则创建"""
    sid = session.get("sid")
    if not sid:
        sid = str(uuid.uuid4())
        session["sid"] = sid
    if sid not in assistants:
        assistants[sid] = TravelAssistant()
    return assistants[sid]


def _run_tool_cycle_stream(assistant: TravelAssistant):
    """ReAct loop that yields SSE event dicts for real-time streaming."""
    tool_call_count = 0
    for i in range(assistant.max_turns):
        yield {"type": "status", "step": i + 1}

        context_prompt = f"\n\n【系统提示】{assistant.get_context_summary(tool_call_count)}"
        system_message = {"role": "system", "content": AGENT_SYSTEM_PROMPT + context_prompt}
        llm_messages = [system_message] + assistant.messages

        # 流式调用 LLM，逐 chunk yield token 事件
        llm_output = ""
        for chunk in llm.generate_stream(llm_messages):
            llm_output += chunk
            yield {"type": "token", "step": i + 1, "content": chunk}

        output_text, _ = _extract_action(llm_output)

        # Extract and emit Thought
        thought_match = re.search(r"Thought:\s*(.*?)(?=\n\s*Action:|\Z)", output_text, re.DOTALL)
        if thought_match:
            yield {"type": "thought", "step": i + 1, "content": thought_match.group(1).strip()}

        # Extract and emit Action
        action_match = re.search(r"Action:\s*(.*)", output_text, re.DOTALL)
        if action_match:
            yield {"type": "action", "step": i + 1, "content": action_match.group(1).strip()}

        assistant.messages.append({"role": "assistant", "content": output_text})
        action_data = _parse_action(output_text)

        if action_data["type"] == "finish":
            yield {"type": "answer", "content": action_data["content"]}
            return

        elif action_data["type"] == "tool":
            tool_call_count += 1
            tool_name = action_data["name"]
            kwargs = action_data["kwargs"]
            if tool_name in available_tools:
                observation = available_tools[tool_name](**kwargs)
            else:
                observation = f"错误：未定义的工具 '{tool_name}'"
            observation = _truncate_observation(observation)
            yield {"type": "observation", "step": i + 1, "content": observation}
            assistant.messages[-1]["content"] += f"\nObservation: {observation}"

        else:
            # LLM 未遵循格式，视为直接回答
            yield {"type": "answer", "content": action_data.get("content", output_text)}
            return

    yield {"type": "answer", "content": "抱歉，我还没有找到满意的答案。请换个方式再试试。"}
    assistant.messages.append({"role": "assistant", "content": "结果：抱歉，我还没有找到满意的答案。请换个方式再试试。"})


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/send", methods=["POST"])
def send():
    data = request.get_json()
    user_input = data.get("message", "").strip()
    if not user_input:
        return {"error": "empty message"}, 400

    assistant = get_assistant()
    assistant.add_message("user", user_input)

    def generate():
        final_answer = None
        for event in _run_tool_cycle_stream(assistant):
            if event["type"] == "answer":
                final_answer = event["content"]
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        if final_answer:
            assistant.add_message("result", final_answer)
            try:
                assistant.save()
            except Exception:
                pass
        yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"

    return Response(generate(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


@app.route("/api/reset", methods=["POST"])
def reset():
    assistant = get_assistant()
    assistant.reset()
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
