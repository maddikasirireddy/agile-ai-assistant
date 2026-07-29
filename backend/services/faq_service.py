import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("agile_wellness")

KNOWLEDGE_DIR = "/Users/sirireddy/agile-ai-assistant/backend/knowledge"

def load_json_file(filename: str) -> Optional[Dict[str, Any]]:
    """Helper to safely read a JSON file from the local knowledge base directory."""
    path = os.path.join(KNOWLEDGE_DIR, filename)
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            logger.warning(f"Knowledge file not found: {path}")
    except Exception as e:
        logger.error(f"Error reading local knowledge file {filename}: {e}")
    return None

def get_shipping_info() -> str:
    """Retrieve and format shipping information."""
    data = load_json_file("shipping.json")
    if not data or "shipping" not in data:
        return "Our standard shipping takes 3-5 business days across India. Free shipping is available for orders above ₹499."
    
    ship = data["shipping"]
    res = "📦 **Shipping & Delivery Information**\n\n"
    res += "**Delivery Times & Fees:**\n"
    for method in ship.get("methods", []):
        res += f"- **{method['name']}**: {method['duration']} | Cost: {method['cost']}\n"
    res += f"\n**Tracking:** {ship.get('tracking')}\n"
    res += f"\n**Shipping Coverage:** {ship.get('locations')}\n"
    res += f"\n**Order Processing Time:** {ship.get('handling_time')}"
    return res

def get_returns_info() -> str:
    """Retrieve and format returns and refunds policies."""
    data = load_json_file("returns.json")
    if not data or "policy" not in data:
        return "We offer a 7-day return policy for unused and unopened products."
        
    policy = data["policy"]
    res = "🔄 **Returns & Refund Policy**\n\n"
    res += f"- **Return Window**: {policy.get('return_window')}\n"
    res += f"- **Refund Processing**: {policy.get('refunds')}\n"
    res += f"- **Order Cancellation**: {policy.get('cancellations')}\n"
    res += f"- **Damaged or Incorrect Items**: {policy.get('damaged_items')}"
    return res

def get_payment_info() -> str:
    """Retrieve and format payment information."""
    data = load_json_file("payment.json")
    if not data or "payment" not in data:
        return "We accept Credit/Debit Cards, UPI, Net Banking, and Cash on Delivery (COD)."
        
    pay = data["payment"]
    res = "💳 **Payment Options**\n\n"
    res += "**Accepted Payment Methods:**\n"
    for method in pay.get("methods", []):
        res += f"- **{method['name']}**: {method['details']}\n"
    res += f"\n**Payment Security:** {pay.get('security')}"
    return res

def get_contact_info() -> str:
    """Retrieve and format support contact details."""
    data = load_json_file("contact.json")
    if not data or "contact" not in data or not data["contact"].get("email") or "support@agilewellness.in" in data["contact"].get("email", ""):
        return "Agile Wellness customer support contact details are not currently configured. Please visit our website for assistance."
        
    c = data["contact"]
    res = "📞 **Contact Support**\n\n"
    res += "We are here to help! You can reach the Agile Wellness team through the following channels:\n\n"
    res += f"- **Email Support**: [{c.get('email')}](mailto:{c.get('email')})\n"
    res += f"- **Phone / WhatsApp**: {c.get('phone')} / {c.get('whatsapp')}\n"
    res += f"- **Operating Hours**: {c.get('hours')}\n"
    res += f"- **Office Address**: {c.get('address')}"
    return res

def get_store_info() -> str:
    """Retrieve and format general store details."""
    data = load_json_file("store_info.json")
    if not data or "store" not in data:
        return "Agile Wellness provides premium organic and natural wellness products."
        
    s = data["store"]
    res = f"🌿 **About {s.get('name')}** — *{s.get('tagline')}*\n\n"
    res += f"{s.get('mission')}\n\n"
    res += f"- **Store Link**: [Visit Our Shop]({s.get('website')})\n"
    if s.get("social"):
        res += f"- **Follow us on Instagram**: [Instagram]({s['social'].get('instagram')})\n"
        res += f"- **Like us on Facebook**: [Facebook]({s['social'].get('facebook')})"
    return res

def lookup_faq_answer(message: str) -> Optional[str]:
    """
    Search the FAQ knowledge base for questions containing words matching the query.
    Returns the mapped answer if a match is found.
    """
    data = load_json_file("faq.json")
    if not data or "questions" not in data:
        return None
        
    msg_lower = message.lower()
    best_match = None
    max_matched_keywords = 0
    
    for q in data["questions"]:
        matched_count = 0
        for kw in q.get("keywords", []):
            if kw.lower() in msg_lower:
                matched_count += 1
        
        if matched_count > max_matched_keywords:
            max_matched_keywords = matched_count
            best_match = q.get("answer")
            
    return best_match
