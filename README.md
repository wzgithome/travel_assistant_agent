# 智能旅行助手

基于 ReAct 风格的中文旅行规划 Agent，通过 LLM 驱动的工具调用循环，为用户提供天气查询、景点推荐、交通指南、美食推荐、预算估算、地图展示和路线规划等一站式旅行服务。

## 演示

```
你：我想去北京玩三天，帮我规划一下行程

Thought: 用户想去北京玩三天，我需要先了解天气情况和是否是节假日...
Action: get_weather_forecast(city="北京", days=3)

Thought: 天气信息已获取，接下来查看是否是节假日...
Action: check_holiday(date_str="2026-05-17")

Thought: 信息已充分，为用户规划行程...
Action: Finish[根据天气和节假日情况，为您规划了三天北京行程...]
```

## 支持的城市

南京、上海、北京、广州、深圳、杭州、成都、重庆、武汉、西安、芜湖

## 内置工具

| 工具 | 数据源 | 说明 |
|------|--------|------|
| `get_current_date()` | - | 获取当前日期和星期 |
| `check_holiday(date_str)` | - | 查询节假日信息 |
| `get_weather(city)` | wttr.in | 实时天气查询 |
| `get_weather_forecast(city, days)` | wttr.in | 未来多天天气预报 |
| `get_attraction(city, weather)` | Tavily | 景点推荐 |
| `get_transport(city)` | Tavily | 交通指南 |
| `get_restaurant(city, cuisine_type)` | Tavily | 美食推荐 |
| `estimate_budget(city, days, travel_style)` | Tavily | 预算估算 |
| `show_map(city, attractions)` | 高德地图 | 景点位置展示 |
| `get_route(city, origin, destination, mode)` | 高德地图 | 路线规划（步行/驾车/公交/地铁） |

## 快速开始

### 1. 环境要求

- Python 3.12
- uv（推荐）或 pip

### 2. 安装依赖

```bash
# 使用 uv（推荐）
uv sync

# 或使用 pip
pip install openai tavily-python requests python-dotenv flask flask-cors
```

### 3. 配置环境变量

在项目根目录创建 `.env` 文件：

```env
OPENAI_API_KEY3=your_openai_api_key
OPENAI_BASE_URL3=your_base_url
TAVILY_API_KEY=your_tavily_api_key
GAODE_API_KEY=your_gaode_api_key
```

> 当前使用的模型为 `kimi-k2.5`，如需切换模型请修改 `config/settings.py` 中的 `MODEL_ID` 及对应的 API Key 和 Base URL。

### 4. 运行

```bash
# CLI 交互式多轮对话
python main.py

# CLI 单轮演示
python main.py --single

# Web UI（Flask + SSE 流式输出）
cd web && python app.py
# 访问 http://localhost:5050
```

## 项目结构

```
Hello-Agent-New/
├── config/
│   ├── __init__.py
│   └── settings.py          # 环境变量与模型配置
├── core/
│   ├── __init__.py
│   ├── prompt.py            # 系统提示词与支持城市列表
│   ├── client.py            # OpenAI 兼容客户端（支持普通/流式生成）
│   └── agent.py             # TravelAssistant Agent 核心逻辑
├── tools/
│   ├── __init__.py
│   ├── date.py              # 日期工具
│   ├── weather.py           # 天气工具
│   ├── holiday.py           # 节假日工具
│   ├── attraction.py        # 景点推荐工具
│   ├── transport.py         # 交通指南工具
│   ├── restaurant.py        # 美食推荐工具
│   ├── budget.py            # 预算估算工具
│   ├── map_api.py           # 高德地图工具（景点位置 + 路线规划）
│   └── registry.py          # 工具注册表
├── utils/
│   ├── __init__.py
│   └── tokenizer.py         # 文本截断工具
├── web/
│   ├── app.py               # Flask SSE 流式 Web 服务
│   └── static/index.html    # 前端聊天界面
├── main.py                  # CLI 入口
├── travel_assistant_agent.py # 兼容层（re-export，保持向后兼容）
├── CLAUDE.md                # 项目开发文档
└── README.md
```

## 工作原理

Agent 采用 **ReAct（Reasoning + Acting）** 模式运行：

```
用户输入 → LLM 思考 → 选择工具 → 执行工具 → 获取结果 → LLM 继续思考 → ... → 输出最终答案
```

1. 用户输入旅行相关问题
2. LLM 根据系统提示词，以 `Thought: ...\nAction: ...` 格式输出推理过程和工具调用
3. Agent 解析并执行工具调用，将结果返回给 LLM
4. LLM 判断信息是否充分，决定继续调用工具或输出最终答案

## Token 优化

- 系统提示词精简至约 350 字符
- 工具返回值截断至 500 字符（`MAX_OBSERVATION_LENGTH`）
- 上下文消息限制为 6 条
- 历史消息自动压缩，长内容截断至 200 字符

## License

MIT