import sys
import os
import asyncio

# Add backend directory to path
sys.path.append("/Users/sirireddy/agile-ai-assistant/backend")

from dotenv import load_dotenv
load_dotenv("/Users/sirireddy/agile-ai-assistant/backend/.env")

from services.knowledge_service import run_hybrid_chat_flow

try:
    print("Testing 'lip butter'...")
    reply, cart = run_hybrid_chat_flow("lip butter", [], [])
    print(f"Reply: {reply}")
    
    print("\nTesting 'Tell me about Neem sooap'...")
    reply2, cart2 = run_hybrid_chat_flow("Tell me about Neem sooap", [], [])
    print(f"Reply: {reply2}")

except Exception as e:
    import traceback
    traceback.print_exc()
