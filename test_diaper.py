import sys
sys.path.append("/Users/sirireddy/agile-ai-assistant/backend")

from dotenv import load_dotenv
load_dotenv("/Users/sirireddy/agile-ai-assistant/backend/.env")

from services.knowledge_service import run_hybrid_chat_flow
from services.session_service import reset_session

def run_tests():
    print("\n=== TEST 1: What can I use for baby diaper rash? ===")
    reset_session("test_diaper")
    r, c = run_hybrid_chat_flow("What can I use for baby diaper rash?", [], [], session_id="test_diaper")
    print(f"Bot: {r}")

    print("\n=== TEST 2: Suggest something for diaper rash. ===")
    reset_session("test_diaper")
    r, c = run_hybrid_chat_flow("Suggest something for diaper rash.", [], [], session_id="test_diaper")
    print(f"Bot: {r}")

    print("\n=== TEST 3: Active Context (Price) ===")
    reset_session("test_diaper")
    r, c = run_hybrid_chat_flow("Tell me about Lavender Soap.", [], [], session_id="test_diaper")
    print(f"Bot 1: {r[:100]}...")
    r, c = run_hybrid_chat_flow("What's the price?", [], [], session_id="test_diaper")
    print(f"Bot 2: {r}")

    print("\n=== TEST 4: Active Context Override (Diaper Rash) ===")
    reset_session("test_diaper")
    r, c = run_hybrid_chat_flow("Tell me about Lavender Soap.", [], [], session_id="test_diaper")
    print(f"Bot 1: {r[:100]}...")
    r, c = run_hybrid_chat_flow("What can I use for baby diaper rash?", [], [], session_id="test_diaper")
    print(f"Bot 2: {r}")

if __name__ == "__main__":
    run_tests()
