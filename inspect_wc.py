import sys
import json
sys.path.append("/Users/sirireddy/agile-ai-assistant/backend")

from dotenv import load_dotenv
load_dotenv("/Users/sirireddy/agile-ai-assistant/backend/.env")

from services.woocommerce_service import wc_service

def inspect():
    products = wc_service.get_products()
    baby_products = []
    
    for p in products:
        name = p.get('name', '').lower()
        desc = p.get('description', '').lower()
        cats = [c.lower() for c in p.get('categories', [])]
        
        if 'baby' in name or 'baby' in desc or any('baby' in c for c in cats):
            baby_products.append(p)
            
    print(f"Total products: {len(products)}")
    print(f"Total baby-related products: {len(baby_products)}")
    
    for p in baby_products:
        print("\n-------------------------")
        print(f"ID: {p.get('id')}")
        print(f"Name: {p.get('name')}")
        print(f"Categories: {p.get('categories')}")
        print(f"Tags: {p.get('tags')}")
        print(f"Concerns: {p.get('concerns')}")
        print(f"Baby Safe: {p.get('baby_safe')}")
        print(f"Description snippet: {p.get('description', '')[:100]}...")

if __name__ == "__main__":
    inspect()
