import sys
import os
sys.path.append("/Users/sirireddy/agile-ai-assistant/backend")

from dotenv import load_dotenv
load_dotenv("/Users/sirireddy/agile-ai-assistant/backend/.env")

from woocommerce import API

api = API(
    url=os.getenv("WC_URL"),
    consumer_key=os.getenv("WC_CONSUMER_KEY"),
    consumer_secret=os.getenv("WC_CONSUMER_SECRET"),
    version="wc/v3"
)

def fetch_all():
    page = 1
    total = 0
    baby_total = 0
    
    while True:
        res = api.get("products", params={"per_page": 100, "page": page, "status": "publish"})
        products = res.json()
        if not products:
            break
            
        total += len(products)
        
        for p in products:
            name = p.get('name', '').lower()
            if 'baby' in name or 'diaper' in name:
                print(f"Found Baby Product: {name} (ID: {p.get('id')})")
                baby_total += 1
                
        page += 1
        
    print(f"Total products across all pages: {total}")
    print(f"Total explicit baby products: {baby_total}")

if __name__ == "__main__":
    fetch_all()
