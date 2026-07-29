import sys
import json
sys.path.append("/Users/sirireddy/agile-ai-assistant/backend")

from dotenv import load_dotenv
load_dotenv("/Users/sirireddy/agile-ai-assistant/backend/.env")

from services.knowledge_service import run_hybrid_chat_flow
from services.session_service import reset_session

def test_flows():
    sid = "test_verification"
    cart = []
    
    print("\n=== TEST 1: Product Details ===")
    reset_session(sid)
    reply1, cart = run_hybrid_chat_flow("Tell me about Charcoal & Lavender Soap.", [], cart, session_id=sid)
    print(f"Bot: {reply1}\n")
    reply2, cart = run_hybrid_chat_flow("Charcoal & Lavender Soap - Handmade", [], cart, session_id=sid)
    print(f"Bot: {reply2}\n")

    print("=== TEST 2: Price ===")
    reset_session(sid)
    reply1, cart = run_hybrid_chat_flow("What is the price of Charcoal & Lavender Soap?", [], cart, session_id=sid)
    print(f"Bot: {reply1}\n")
    reply2, cart = run_hybrid_chat_flow("Charcoal & Lavender Soap - Handmade", [], cart, session_id=sid)
    print(f"Bot: {reply2}\n")

    print("=== TEST 3: Add to Cart ===")
    reset_session(sid)
    reply1, cart = run_hybrid_chat_flow("Add Charcoal & Lavender Soap to my cart.", [], cart, session_id=sid)
    print(f"Bot: {reply1}\n")
    reply2, cart = run_hybrid_chat_flow("Charcoal & Lavender Soap - Handmade", [], cart, session_id=sid)
    print(f"Bot: {reply2}\n")

if __name__ == "__main__":
    test_flows()
