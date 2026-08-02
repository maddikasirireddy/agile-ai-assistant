import sys
import os

# Add backend directory to path
sys.path.append("/Users/sirireddy/agile-ai-assistant/backend")

from dotenv import load_dotenv
load_dotenv("/Users/sirireddy/agile-ai-assistant/backend/.env")

from services.woocommerce_service import wc_service

try:
    products = wc_service.get_products(force_refresh=True)
    print(f"Total products: {len(products)}")
    if products:
        p = products[0]
        print(f"Enriched Product keys: {p.keys()}")
        print(f"Categories: {p.get('categories')}")
        print(f"Tags: {p.get('tags')}")
        print(f"Images: {p.get('images')}")
        
    print("\n--- RAW API RESPONSE TEST ---")
    response = wc_service.api.get("products", params={"per_page": 1, "status": "publish"})
    if response.status_code in (200, 201):
        raw_p = response.json()[0]
        print(f"Raw Categories: {raw_p.get('categories')}")
        print(f"Raw Tags: {raw_p.get('tags')}")
        print(f"Raw Images: {raw_p.get('images')}")
except Exception as e:
    import traceback
    traceback.print_exc()
