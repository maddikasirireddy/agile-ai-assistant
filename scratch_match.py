import re

candidates = [
    {"name": "Charcoal & Lavender Soap - Handmade"},
    {"name": "Lavender Soap - Handmade"}
]
user_text = "Charcoal & Lavender Soap - Handmade"
text = user_text.lower().strip()

print(f"text: '{text}'")

for p in candidates:
    name = p.get("name", "").lower()
    clean_name = re.sub(r"\s*[\(\-\[].*$", "", name).strip()
    print(f"\n--- Checking '{name}' ---")
    print(f"clean_name: '{clean_name}'")
    print(f"name in text: {name in text}")
    print(f"clean_name in text: {clean_name in text}")
