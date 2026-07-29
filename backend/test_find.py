import re
from typing import List, Dict, Any

def normalize_string(s: str) -> str:
    return re.sub(r"[^\w]", "", s.lower())

def find_matching_products(message: str, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    msg = message.lower().strip()
    msg_words = set(re.findall(r"\w+", msg))
    
    synonym_map = {
        "lipbalm": "lip butter",
        "lip balm": "lip butter",
        "lipbutter": "lip butter",
        "lip butter": "lip butter",
        "neem soap": "neem soap",
        "charcoal soap": "charcoal soap",
        "lavender soap": "lavender soap",
        "onion shampoo": "onion shampoo",
        "orange powder": "orange peel powder"
    }
    
    query_term = msg
    for syn, target in synonym_map.items():
        if syn in msg:
            query_term = msg.replace(syn, target)
            break

    query_term = re.sub(
        r"\b(what is the price of|what is|price of|how do i use|how to use|is|in stock|available|ingredients in|whats in|what is in|composition of|where is|add|remove|delete|buy|purchase|tell me about|tell me|show me|details on|info on|information on|whats|what|to my cart|to cart|in my cart|in cart|from my cart|from cart|into my cart|into cart)\b", 
        "", 
        query_term
    ).strip()
    query_term = re.sub(r"[^\w\s\-\&]", "", query_term).strip()
    
    exact_matches = []
    close_matches = []
    
    generic_words = {"soap", "shampoo", "powder", "oil", "butter", "lotion", "serum", "cream", "wellness"}
    
    sorted_products = sorted(products, key=lambda x: len(x.get("name", "")), reverse=True)
    
    for p in sorted_products:
        name = p.get("name", "").lower()
        clean_name = re.sub(r"\s*[\(\[].*$", "", name).strip()
        clean_name = re.sub(r"\s+\-\s+.*$", "", clean_name).strip()
        
        if len(query_term) > 3:
            if normalize_string(query_term) == normalize_string(clean_name):
                exact_matches.append(p)
                continue
            if normalize_string(query_term) in normalize_string(clean_name) or normalize_string(clean_name) in normalize_string(query_term):
                exact_matches.append(p)
                continue

        if clean_name in generic_words:
            continue
            
        if clean_name in msg or name in msg:
            exact_matches.append(p)
            continue

        clean_words = set(re.findall(r"\w+", clean_name))
        significant_words = {w for w in clean_words if w not in generic_words}
        if significant_words and significant_words.issubset(msg_words):
            close_matches.append(p)

    matches = exact_matches if exact_matches else close_matches
    
    unique_matches = []
    seen = set()
    for p in matches:
        if p["id"] not in seen:
            unique_matches.append(p)
            seen.add(p["id"])
            
    return unique_matches

products = [
    {"id": 9325, "name": "Neem Soap - Handmade"}
]
print(find_matching_products("Tell me about Neem sooap", products))
print(find_matching_products("Neem sooap", products))
