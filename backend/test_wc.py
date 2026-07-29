import os
from dotenv import load_dotenv
from woocommerce import API

load_dotenv(dotenv_path=".env")

wcapi = API(
    url=os.getenv("WC_URL"),
    consumer_key=os.getenv("WC_CONSUMER_KEY"),
    consumer_secret=os.getenv("WC_CONSUMER_SECRET"),
    version="wc/v3",
)

print("Connecting to WooCommerce...")

response = wcapi.get("products", params={"per_page": 5})

print("Status:", response.status_code)
print(response.text)