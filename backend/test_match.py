import sys
import os

# Add backend directory to path
sys.path.append("/Users/sirireddy/agile-ai-assistant/backend")

from dotenv import load_dotenv
load_dotenv("/Users/sirireddy/agile-ai-assistant/backend/.env")

from services.knowledge_service import find_matching_products
from services.woocommerce_service import wc_service

try:
    products = wc_service.get_products()
    print("Testing 'mango lip butter'...")
    matches = find_matching_products("mango lip butter", products)
    print(f"Matches found: {len(matches)}")
    for m in matches:
        print(f"- {m['name']}")
        
    print("\nTesting 'neem face wash'...")
    matches2 = find_matching_products("neem face wash", products)
    print(f"Matches found: {len(matches2)}")
    for m in matches2:
        print(f"- {m['name']}")
except Exception as e:
    import traceback
    traceback.print_exc()
