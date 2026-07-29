import sys
sys.path.append("/Users/sirireddy/agile-ai-assistant/backend")

from dotenv import load_dotenv
load_dotenv("/Users/sirireddy/agile-ai-assistant/backend/.env")

from services.knowledge_service import run_hybrid_chat_flow
from services.cache_service import global_cache

# Invalidate cache to force re-enrichment
global_cache.invalidate("wc_products_catalog")

queries = [
    "Do you have baby products?",
    "Suggest some baby products",
    "What baby soaps do you have?",
    "Suggest a baby shampoo",
    "What can I use for baby diaper rash?",
    "Suggest a soap for acne"
]

for i, q in enumerate(queries, 1):
    print(f"\n=== TEST {i}: {q} ===")
    reply, cart = run_hybrid_chat_flow(q, [], [], session_id=f"test_session_{i}")
    print(f"Bot: {reply}")

