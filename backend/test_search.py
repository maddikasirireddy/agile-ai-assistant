import sys
import os

# Add backend directory to path
sys.path.append("/Users/sirireddy/agile-ai-assistant/backend")

from dotenv import load_dotenv
load_dotenv("/Users/sirireddy/agile-ai-assistant/backend/.env")

from services.gemini_service import search_product

try:
    print("Running search_product for neem sooap...")
    result = search_product("Neem sooap")
    print(f"Result: {result}")
except Exception as e:
    import traceback
    traceback.print_exc()
