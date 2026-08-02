import sys
import os

# Add backend directory to path
sys.path.append("/Users/sirireddy/agile-ai-assistant/backend")

from dotenv import load_dotenv
load_dotenv("/Users/sirireddy/agile-ai-assistant/backend/.env")

from services.search_service import search_products_local
from services.woocommerce_service import wc_service

def run_tests():
    try:
        products = wc_service.get_products()
        print(f"Total products loaded: {len(products)}\n")
        
        queries = [
            "lip butter",
            "mango lip butter",
            "neem soap",
            "neem sooap",
            "baby lotion",
            "cracked lips",
            "oily skin",
            "anti acne"
        ]
        
        for q in queries:
            print(f"=====================================")
            print(f"Query: '{q}'")
            print(f"=====================================")
            matches = search_products_local(products, q)
            if not matches:
                print("No matches found.")
            else:
                for idx, m in enumerate(matches):
                    # Only show top 5 matches
                    if idx >= 5:
                        break
                    score = m.get('_search_score', 0)
                    print(f"[{score:.1f}] {m.get('name')}")
            print("\n")

    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_tests()
