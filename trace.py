import sys
import logging
sys.path.append("/Users/sirireddy/agile-ai-assistant/backend")

from dotenv import load_dotenv
load_dotenv("/Users/sirireddy/agile-ai-assistant/backend/.env")

# Force logging to console
logger = logging.getLogger("agile_wellness")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

from services.knowledge_service import run_hybrid_chat_flow
from services.session_service import reset_session

def trace_it():
    sid = "test_trace_session"
    cart = []
    
    print("\n[USER]: Tell me about Charcoal & Lavender Soap.")
    reset_session(sid)
    reply1, cart = run_hybrid_chat_flow("Tell me about Charcoal & Lavender Soap.", [], cart, session_id=sid)
    
    print("\n[USER]: Charcoal & Lavender Soap - Handmade")
    reply2, cart = run_hybrid_chat_flow("Charcoal & Lavender Soap - Handmade", [], cart, session_id=sid)

if __name__ == "__main__":
    trace_it()
