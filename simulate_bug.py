import requests
import json

url = "http://127.0.0.1:8000/chat"

# Request 1
req1 = {
    "message": "Recommend a soap for acne.",
    "customer_id": 54,
    "history": [],
    "cart": []
}
print("--- REQUEST 1 ---")
r1 = requests.post(url, json=req1)
print(r1.json()["reply"])

# Request 2
req2 = {
    "message": "Tell me about that product.",
    "customer_id": 54,
    "history": [
        {"role": "user", "text": "Recommend a soap for acne."},
        {"role": "ai", "text": r1.json()["reply"]}
    ],
    "cart": []
}
print("\n--- REQUEST 2 ---")
r2 = requests.post(url, json=req2)
print(r2.json()["reply"])
