import re
import logging

logger = logging.getLogger("agile_wellness")

def classify_intent(message: str) -> str:
    """
    Classifies a user message into one of 20+ e-commerce intent categories.
    Does not call the Gemini API, maintaining low latency.
    """
    msg = message.lower().strip()
    
    # 1. Greetings
    if re.match(r"\b(hi|hello|hey|greetings|hola|good morning|good afternoon|good evening|yo)\b", msg):
        return "greeting"
        
    # 2. Goodbye
    if re.match(r"\b(bye|goodbye|see you|tc|take care|exit|quit|talk later|adios)\b", msg):
        return "goodbye"
        
    # 3. Thanks
    if re.match(r"\b(thanks|thank you|ty|thank|great|perfect|awesome|helpful|appreciated|appreciate)\b", msg):
        return "thanks"

    # 4. Shopping Actions (High Priority)
    
    # 4a. Add to Cart
    if any(term in msg for term in ["add to cart", "add it", "add this", "put in cart", "add to my cart", "add to basket"]):
        return "add_to_cart"
    if msg.startswith("add ") and not any(term in msg for term in ["more", "less", "qty", "quantity"]):
        return "add_to_cart"
        
    # 4b. Remove from Cart
    if any(term in msg for term in ["remove from cart", "remove it", "remove this", "delete from cart", "delete it", "take out"]):
        return "remove_from_cart"
    if msg.startswith("remove ") or msg.startswith("delete "):
        return "remove_from_cart"
        
    # 4c. Buy Now / Buy This
    if any(term in msg for term in ["buy now", "buy this", "buy it", "purchase this", "purchase it"]):
        return "buy_now"
    if msg.startswith("buy ") and not any(term in msg for term in ["more", "less"]):
        return "buy_now"

    # 4d. View Cart
    if any(term in msg for term in ["view cart", "show cart", "my cart", "viewing cart", "whats in my cart", "items in cart"]):
        return "view_cart"

    # 4e. Checkout
    if any(term in msg for term in ["checkout", "check out", "proceed to pay", "pay now"]):
        return "checkout"

    # 4f. Quantity Change
    qty_patterns = [
        r"\bincrease\s+quantity\b", r"\bdecrease\s+quantity\b", r"\bchange\s+quantity\b",
        r"\badd\s+\d+\s+more\b", r"\bchange\s+qty\b", r"\bmore\s+quantity\b",
        r"\bqty\s+to\s+\d+\b", r"\bquantity\s+to\s+\d+\b"
    ]
    if any(re.search(pat, msg) for pat in qty_patterns) or any(term in msg for term in ["increase", "decrease", "more of", "less of"]):
        return "quantity_change"

    # 5. Order status & Tracking
    order_patterns = [
        r"\btrack\s+order\b", r"\border\s+#?\d+\b", r"\bwhere\s+is\s+my\s+.*order\b", 
        r"\border\s+status\b", r"\bpackage\s+status\b", r"\bpackage\s+location\b", 
        r"\border\s+tracking\b", r"\bwhere\s+is\s+my\s+.*package\b", r"\bshipping\s+status\b"
    ]
    if any(re.search(pat, msg) for pat in order_patterns) or ("where" in msg and any(term in msg for term in ["package", "order", "parcel", "delivery"])):
        return "order_status"
        
    # 6. Shipping & Delivery FAQs
    shipping_keywords = ["shipping", "delivery", "dispatch", "deliver", "shipment", "transit", "courier", "charges", "postage"]
    if any(kw in msg for kw in shipping_keywords):
        return "shipping"
        
    # 7. Returns & Refunds FAQs
    returns_keywords = ["return", "refund", "exchange", "cancel", "cancellation", "replace", "damaged product", "policy"]
    if any(kw in msg for kw in returns_keywords):
        return "returns"
        
    # 8. Payment & COD FAQs
    payment_keywords = ["payment", "pay", "upi", "gpay", " razorpay", "cod", "cash on delivery", "credit card", "debit card"]
    if any(kw in msg for kw in payment_keywords):
        return "payment"
        
    # 9. Contact details FAQ
    contact_keywords = ["contact", "support", "email", "phone", "number", "call", "address", "location", "reach out"]
    if any(kw in msg for kw in contact_keywords):
        return "contact"
        
    # 10. Store details & Opening hours FAQ
    store_info_keywords = ["about store", "about you", "who are you", "what is agile wellness", "working hours", "open time", "store info", "mission", "story"]
    if any(kw in msg for kw in store_info_keywords):
        return "store_information"

    # 11. Reorder
    if "reorder" in msg:
        return "latest_order" if "last" in msg or "recent" in msg else "order_status"

    # 12. Specific product query intents
    
    # 12a. Ingredients
    ing_keywords = ["ingredient", "ingredients", "contain", "contains", "contents", "composition", "formula", "made of", "make up", "what is in", "whats in"]
    if any(kw in msg for kw in ing_keywords):
        return "ingredient_information"
        
    # 12b. Product Price
    price_keywords = ["price", "prices", "how much", "cost", "costs", "rate", "rates", "pricing", "value", "mrp"]
    if any(kw in msg for kw in price_keywords):
        return "product_price"
        
    # 12c. Availability / Stock
    stock_keywords = ["stock", "in stock", "available", "availability", "sold out", "out of stock", "can i buy", "purchasable"]
    if any(kw in msg for kw in stock_keywords):
        return "product_availability"
        
    # 12d. Usage / Instructions
    usage_keywords = ["how to use", "use", "usage", "apply", "application", "how to apply", "directions", "instructions", "daily"]
    if any(kw in msg for kw in usage_keywords) and not any(term in msg for term in ["cod", "pay"]):
        return "product_usage"
        
    # 13. General concern matching and recommendations
    skin_keywords = ["skin", "face", "acne", "pimple", "wrinkle", "aging", "glowing", "moisturizer", "toner", "scrub", "mitti", "brighten"]
    if any(kw in msg for kw in skin_keywords):
        return "skincare"
        
    hair_keywords = ["hair", "scalp", "dandruff", "fall", "shampoo", "conditioner", "shikakai", "bhringraj", "onion"]
    if any(kw in msg for kw in hair_keywords):
        return "haircare"
        
    baby_keywords = ["baby", "infant", "child", "kids", "cradle", "newborn"]
    if any(kw in msg for kw in baby_keywords):
        return "babycare"
        
    rec_keywords = ["recommend", "suggest", "suitable for", "what should i", "choose", "best for"]
    if any(kw in msg for kw in rec_keywords):
        return "product_recommendation"
        
    info_keywords = ["tell me about", "what is", "show me", "catalog", "products", "items", "soap", "powder"]
    if any(kw in msg for kw in info_keywords):
        return "product_information"
        
    faq_keywords = ["faq", "question", "organic", "natural", "certified", "testing", "animal testing"]
    if any(kw in msg for kw in faq_keywords):
        return "faq"
        
    return "unknown"
