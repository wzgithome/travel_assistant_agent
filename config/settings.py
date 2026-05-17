import os
import dotenv

dotenv.load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY3")
BASE_URL = os.getenv("OPENAI_BASE_URL3")
MODEL_ID = "kimi-k2.5"

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if TAVILY_API_KEY:
    os.environ['TAVILY_API_KEY'] = TAVILY_API_KEY

GAODE_API_KEY = os.getenv("GAODE_API_KEY")
