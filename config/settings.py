import os
import dotenv

dotenv.load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY2")
BASE_URL = os.getenv("OPENAI_BASE_URL2")
MODEL_ID = "qwen3.7-plus"

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if TAVILY_API_KEY:
    os.environ['TAVILY_API_KEY'] = TAVILY_API_KEY

GAODE_API_KEY = os.getenv("GAODE_API_KEY")
