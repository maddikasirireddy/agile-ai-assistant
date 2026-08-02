import sys
sys.path.append("/Users/sirireddy/agile-ai-assistant/backend")
from dotenv import load_dotenv
load_dotenv("/Users/sirireddy/agile-ai-assistant/backend/.env")
from services.woocommerce_service import wc_service

products = wc_service.get_products()
categories = set()
tags = set()
for p in products:
    for c in p.get('categories', []):
        categories.add(c)
    for t in p.get('tags', []):
        tags.add(t)

print("Categories:")
for c in categories:
    print(c)
print("\nTags:")
for t in tags:
    print(t)
