import sys
from core.agent import TravelAssistant, _run_tool_cycle
from core.prompt import SUPPORTED_CITIES


def run_interactive():
    """启动交互式多轮对话会话"""
    assistant = TravelAssistant()
    assistant.load()

    print("=" * 60)
    print("🌤️ 欢迎使用智能旅行助手！")
    print(f"💡 支持的预设城市：{', '.join(SUPPORTED_CITIES)}")
    print("📝 可用指令：exit (退出), clear (清空记录), help (帮助)")
    print("=" * 60 + "\n")

    while True:
        try:
            user_input = input("你：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 再见！\n")
            break

        if user_input.lower() in ['exit', 'quit', 'q']:
            print("👋 再见！\n")
            break
        elif user_input.lower() == 'clear':
            assistant.reset()
            continue
        elif user_input.lower() == 'help':
            print("""\n📖 使用指南:
   • 直接输入问题，例如："查询北京的天气"
   • 可以结合上文，例如："那上海呢？"（会继承上下文）
   • clear - 清空对话历史
   • exit - 退出程序
   """)
            continue

        if not user_input:
            continue

        assistant.add_message("user", user_input)
        final_answer = _run_tool_cycle(assistant)
        assistant.add_message("result", final_answer)
        assistant.save()

        print(f"\n{'=' * 60}\n")


def run_single_turn(user_prompt: str) -> list:
    """运行单次对话"""
    assistant = TravelAssistant()
    assistant.add_message("user", user_prompt)

    print(f"用户输入：{user_prompt}\n" + "=" * 40)

    final_answer = _run_tool_cycle(assistant, verbose=True)
    assistant.add_message("result", final_answer)

    return assistant.messages


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--single":
        user_prompt = "你好，请帮我查询一下今天北京的天气，然后根据天气推荐一个合适的旅游景点。"
        run_single_turn(user_prompt)
    else:
        run_interactive()
