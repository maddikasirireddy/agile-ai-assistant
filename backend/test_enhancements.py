import sys
sys.path.append("/Users/sirireddy/agile-ai-assistant/backend")
from dotenv import load_dotenv
load_dotenv("/Users/sirireddy/agile-ai-assistant/backend/.env")

from services.knowledge_service import run_hybrid_chat_flow
from services.search_service import search_products_local
from services.woocommerce_service import wc_service
import re

queries = [
    "Show soaps under ₹250",
    "Add 2 neem soaps",
    "Products with charcoal",
    "Track my order",
    "Reorder my last purchase"
]

report = "# Retrieval Engine Enhancements: Validation Report\n\n"

for q in queries:
    history = []
    q = q.strip()
    if not q:
        continue
    
    # Sleep to avoid rate limits
    import time
    time.sleep(4)
    
    cart = []
    customer_id = 123
    
    # Let's seed history or target_product if needed for add_to_cart?
    # "Add 2 neem soaps" -> intent is add_to_cart, but run_hybrid_chat_flow resolves product first!
    scored_matches = search_products_local(wc_service.get_products(), q)
    print(f"Debug: {q} -> Top 3 scores:")
    for p in scored_matches[:3]:
        print(f"  {p['name']}: {p.get('_search_score')}")

    reply, new_cart = run_hybrid_chat_flow(q, history, cart, customer_id=customer_id)
    
    report += f"### Query: `{q}`\n"
    report += f"**Bot Reply:**\n> {reply.replace(chr(10), chr(10) + '> ')}\n\n"
    
    if new_cart:
        report += f"**Cart Updates:**\n"
        for item in new_cart:
            report += f"- {item['quantity']}x {item['name']}\n"
        report += "\n"

with open("/Users/sirireddy/.gemini/antigravity-ide/brain/396fe7ee-56d2-4e70-b3af-b718a1597c05/enhancement_report.md", "w") as f:
    f.write(report)

print("Enhancement report generated.")
