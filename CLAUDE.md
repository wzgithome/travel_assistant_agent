# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Chinese-language travel assistant agent using a ReAct-style tool-calling loop. The agent analyzes user requests and sequentially invokes tools to gather date, weather, attractions, transport, restaurant, hotel, budget, map, and route information for 11 preset Chinese cities (上海、北京、广州、深圳、南京、杭州、成都、重庆、武汉、西安、芜湖).

## Running

```bash
# CLI (new entry point)
python main.py                 # interactive multi-turn
python main.py --single        # single-turn demo

# CLI (compat entry point, same behavior)
python travel_assistant_agent.py
python travel_assistant_agent.py --single

# Web UI (Flask + SSE streaming)
cd web && python app.py
# Then visit http://localhost:5050
```

## Environment & Dependencies

- Python 3.12
- Required packages: `openai`, `tavily-python`, `requests`, `python-dotenv`, `flask`, `flask-cors`
- `.env` is loaded from the project root directory
- Required env vars: `OPENAI_API_KEY3`, `OPENAI_BASE_URL3`, `TAVILY_API_KEY`, `GAODE_API_KEY`
- Current LLM model: **kimi-k2.5** (configured in `config/settings.py`)
- To switch models, change `MODEL_ID` and the corresponding `OPENAI_API_KEY`/`OPENAI_BASE_URL` env vars

## Architecture

```
Hello-Agent-New/
├── config/
│   ├── __init__.py
│   └── settings.py         # 环境变量加载 (API_KEY, BASE_URL, MODEL_ID, GAODE_API_KEY)
├── core/
│   ├── __init__.py
│   ├── prompt.py            # AGENT_SYSTEM_PROMPT, SUPPORTED_CITIES
│   ├── client.py            # OpenAICompatibleClient (generate + generate_stream)
│   └── agent.py             # TravelAssistant, _extract_action, _parse_action, _run_tool_cycle, llm
├── tools/
│   ├── __init__.py
│   ├── date.py              # get_current_date (日期星期)
│   ├── weather.py           # get_weather + get_weather_forecast (wttr.in)
│   ├── holiday.py           # check_holiday (内置节假日数据)
│   ├── attraction.py        # get_attraction (Tavily)
│   ├── transport.py         # get_transport (Tavily)
│   ├── restaurant.py        # get_restaurant (Tavily)
│   ├── hotel.py             # get_hotel (Tavily)
│   ├── budget.py            # estimate_budget (Tavily)
│   ├── map_api.py           # show_map + get_route (高德地图)
│   └── registry.py          # available_tools 字典
├── utils/
│   ├── __init__.py
│   └── tokenizer.py         # MAX_OBSERVATION_LENGTH, _truncate_observation
├── web/
│   ├── app.py               # Flask SSE streaming 服务
│   └── static/index.html    # 前端聊天 UI
├── main.py                  # 新入口 (CLI)
└── travel_assistant_agent.py # 兼容层 (re-export，确保 web/app.py 无需改动)
```

### Tools

| Tool | API | Description |
|------|-----|-------------|
| `get_current_date()` | — | 当前日期和星期 |
| `check_holiday(date_str)` | — | 查询节假日（内置 2026 年法定假日数据） |
| `get_weather(city)` | wttr.in | 实时天气 |
| `get_weather_forecast(city, days)` | wttr.in | 未来几天天气预报 |
| `get_attraction(city, weather)` | Tavily | 景点推荐 |
| `get_transport(city)` | Tavily | 交通指南 |
| `get_restaurant(city, cuisine_type)` | Tavily | 美食推荐 |
| `get_hotel(city, budget_level)` | Tavily | 住宿推荐 |
| `estimate_budget(city, days, travel_style)` | Tavily | 预算估算 |
| `show_map(city, attractions)` | 高德地图 | 景点位置 |
| `get_route(city, origin, destination, mode)` | 高德地图 | 路线规划 |

### Web UI: `web/app.py` + `web/static/index.html`

- Flask app serving a chat UI on port 5050
- Per-session assistant via Flask session + UUID, stored in `assistants` dict (avoids concurrent user interference)
- SSE streaming: `_run_tool_cycle_stream()` uses `generate_stream()` to yield LLM tokens in real-time
- Frontend: raw streaming tokens hidden during tool call steps; structured tool-call cards displayed directly; completed cards stay visible with lower opacity (no auto-collapse)
- Imports from `travel_assistant_agent.py` (compat layer re-exports)

## Key Conventions

- All user-facing text is in Simplified Chinese.
- The LLM output must follow `Thought: ...\nAction: ...` format; `_extract_action` uses regex to truncate extra pairs.
- Tool call parsing: `function_name(arg_name="arg_value")` via regex in `_parse_action`.
- Bus/transit routing prefers subway routes (地铁) when available, scored with a 0.8 time-weight bonus.

## Token Optimization

- System prompt compressed (~350 chars, down from ~600)
- `MAX_OBSERVATION_LENGTH = 500`: tool return values truncated before adding to context
- `context_messages_limit = 6` (down from 10)
- `_compress_old_messages()`: old assistant messages compressed — `Finish[...]` kept as final answer only, long messages truncated to 200 chars
- User messages no longer prefixed with "用户请求："
- Result messages no longer prefixed with "结果："

## Bug Fixes

1. **Per-session assistant** (web app): replaced global `assistant = TravelAssistant()` with per-session dict keyed by UUID via Flask session, preventing concurrent user interference.
2. **Finish regex**: changed from greedy `(.*)` to lazy `(.*?)` in `_compress_old_messages` to correctly handle answers containing `]`.
3. **Debug mode removed**: `app.run(debug=True)` changed to `app.run()` to prevent exposing the interactive debugger in production.
4. **Invalid action handling**: when LLM output doesn't follow `Thought:/Action:` format (e.g. direct answers to non-travel questions), treat as final answer instead of appending error observation and looping.
5. **Excessive tool calls**: strengthened system prompt to require single-tool-call-then-Finish for simple queries.
6. **Frontend display collapse**: removed auto-collapse of previous tool cards (completed cards stay visible with lower opacity); removed max-height limit on tool card body; hidden raw streaming tokens during tool call steps to avoid jarring flash of Thought:/Action: text.
7. **Multi-turn display breakage**: added `done` SSE event from backend (always sent regardless of code path); frontend tracks `gotAnswer` flag and falls back to showing raw LLM output if no `answer` event received; `assistant.save()` wrapped in try/except to prevent blocking response.

## Refactoring

- `travel_assistant_agent.py` (800 lines) split into modular structure: `config/`, `core/`, `tools/`, `utils/`
- `travel_assistant_agent.py` kept as compatibility re-export layer so `web/app.py` needs no changes
- New entry point: `main.py` (replaces the old `if __name__` block)

