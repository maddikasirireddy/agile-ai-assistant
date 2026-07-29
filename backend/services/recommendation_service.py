import re
import logging
from typing import List, Dict, Any, Tuple, Optional
from services.woocommerce_service import wc_service

logger = logging.getLogger("agile_wellness")

# Concern Synonym Maps for Scoring
CONCERN_KEYWORDS = {
    "dry skin": ["dry skin", "dryness", "dehydrated", "moisturize", "hydrate", "flaky skin"],
    "oily skin": ["oily skin", "oil control", "sebum", "clogged pores", "greasy skin", "excess oil"],
    "acne": ["acne", "pimple", "pimples", "breakout", "spots", "blemish"],
    "sensitive skin": ["sensitive skin", "sensitive", "irritated skin", "redness", "gentle"],
    "pigmentation": ["pigmentation", "dark spot", "spots", "uneven tone", "blemishes", "brighten"],
    "tan removal": ["tan", "detan", "de-tan", "tan removal"],
    "diaper rash": ["diaper rash", "rash from diapers", "diaper irritation", "diaper area rash", "cream for diaper rash", "what to use for diaper rash"],
    "baby care": ["baby", "infant", "child", "kids", "cradle", "newborn", "gentle"],
    "hair fall": ["hair fall", "hair loss", "hair growth", "thinning", "roots", "strengthen"],
    "dandruff": ["dandruff", "flaky scalp", "itchy scalp", "anti-dandruff"],
    "dry hair": ["dry hair", "damaged hair", "frizzy", "rough hair", "conditioner"],
    "oily scalp": ["oily scalp", "oily hair", "greasy scalp", "clarifying"]
}

def extract_concern(message: str) -> Optional[str]:
    """Extracts the primary customer concern from the query message."""
    msg = message.lower()
    for concern, keywords in CONCERN_KEYWORDS.items():
        if concern in msg:
            return concern
        for kw in keywords:
            if kw in msg:
                return concern
    
    if "hair" in msg or "shampoo" in msg:
        return "hair care generic"
    if "skin" in msg or "face" in msg or "soap" in msg:
        return "skin care generic"
        
    return None

def check_metadata_contradiction(concern: str, p: Dict[str, Any]) -> bool:
    """
    Returns True if product metadata explicitly conflicts with the concern.
    Utilizes structured avoid_for, skin_types, and body_area properties.
    """
    avoid_list = p.get("avoid_for", [])
    skin_types = p.get("skin_types", [])
    hair_types = p.get("hair_types", [])
    body_area = p.get("body_area", "body")
    p_name = p.get("name", "").lower()
    desc_lower = p.get("description", "").lower()

    # 1. Dry skin contradictions
    if concern == "dry skin":
        if "very dry skin" in avoid_list or "dry skin" in avoid_list:
            return True
        if "oily" in skin_types and "dry" not in skin_types:
            return True

    # 2. Oily skin contradictions
    if concern == "oily skin":
        if "oily skin" in avoid_list:
            return True
        if "dry" in skin_types and "oily" not in skin_types:
            return True

    # 3. Baby care contradictions
    if concern == "baby care":
        # Reject if it's explicitly an adult product despite category mapping
        adult_keywords = ["anti-aging", "deaging", "de-aging", "mocha", "coffee", "charcoal", "tan removal", "acne", "pimple", "blemish", "brightening", "perfume", "fragrance"]
        if any(kw in p_name or kw in desc_lower for kw in adult_keywords):
            return True
        if not p.get("baby_safe", False) or "baby skin" in avoid_list:
            return True

    # 4. Hair care contradictions
    if concern in ["hair fall", "dandruff", "dry hair", "oily scalp", "hair care generic"]:
        if body_area == "face" or body_area == "lips":
            return True

    # 5. Skin care contradictions
    if concern in ["dry skin", "oily skin", "acne", "sensitive skin", "pigmentation", "tan removal", "skin care generic"]:
        if body_area == "hair" and "shampoo" in p_name:
            return True

    return False

def generate_explanation(concern: str, product: Dict[str, Any]) -> str:
    """Generates a dynamic, explainable reason based on structured product metadata."""
    ingredients = [i.lower() for i in product.get("ingredients", [])]
    benefits = [b.lower() for b in product.get("benefits", [])]
    
    if concern == "dry skin":
        for ing in ["almond", "coconut", "aloe", "shea butter", "butter"]:
            if ing in ingredients:
                return f"Recommended because it contains nourishing {ing} which deeply hydrates and restores dry skin."
        return "Recommended because it contains moisturizing ingredients designed to soothe dry and flaky skin."
        
    elif concern in ["oily skin", "acne"]:
        for ing in ["neem", "tea tree", "charcoal", "multani mitti"]:
            if ing in ingredients:
                return f"Recommended because it contains {ing} which regulates excess sebum and helps prevent acne breakouts."
        return "Recommended because it clarifies pores and regulates oil without drying your skin."
        
    elif concern == "sensitive skin":
        return "Recommended because it is 100% natural, mild, and formulated to calm sensitive skin."
        
    elif concern == "baby care":
        if product.get("categories") and any("baby" in c for c in product.get("categories", [])):
            return "Recommended because the product is listed in the baby care category."
        elif any("baby" in t for t in product.get("tags", [])):
            return "Recommended because the product is tagged for baby use."
        elif "baby" in product.get("description", "").lower() or "baby" in product.get("name", "").lower():
            return "Recommended because the product description explicitly identifies it for baby care."
        return "Recommended because it contains organic, gentle ingredients."
        
    elif concern == "dandruff":
        for ing in ["onion", "tea tree", "shikakai"]:
            if ing in ingredients:
                return f"Recommended because it contains {ing} to target dandruff flakes and soothe an itchy scalp."
        return "Recommended because it helps balance scalp oils and eliminates dandruff flakes naturally."
        
    elif concern == "hair fall":
        for ing in ["bhringraj", "amla", "shikakai", "onion"]:
            if ing in ingredients:
                return f"Recommended because it contains active {ing} which strengthens roots and reduces hair fall."
        return "Recommended because it nourishes the scalp and stimulates healthy hair growth."
        
    elif concern == "dry hair":
        return "Recommended because it locks in moisture to repair damaged, dry, or frizzy hair shafts."
        
    if benefits:
        return f"Recommended because it naturally targets {', '.join(benefits[:2])}."
    return "Recommended based on organic ingredient suitability for your wellness goals."

def get_product_recommendations(message: str) -> str:
    """
    Scores catalog products using structured metadata properties first,
    and product description text keywords second.
    Ranks products, excludes conflicts, and returns the top 3 matches with explanations.
    """
    products = wc_service.get_products()
    if not products:
        return "We have wonderful organic products in our catalog. Currently, we are updating our store. Please try again shortly.", None

    concern = extract_concern(message)
    logger.info(f"Recommendation Engine: Extracted concern '{concern}' from query.")

    scored_products: List[Tuple[float, Dict[str, Any]]] = []

    for p in products:
        # Check strict contradiction first using metadata
        if concern and check_metadata_contradiction(concern, p):
            continue

        score = 0.0
        name_lower = p.get("name", "").lower()
        desc_lower = (p.get("description", "") + " " + p.get("short_description", "")).lower()

        # --------------------------------------------------
        # STAGE 1: Structured Metadata Matching (Highest Weight)
        # --------------------------------------------------
        if concern:
            # Check recommended_for list (populated dynamically from skin_types, hair_types, concerns, baby_safe)
            if concern in p.get("recommended_for", []):
                score += 15.0
            
            # Explicit type lists match
            if concern in ["dry skin", "oily skin", "sensitive skin"] and concern.replace(" skin", "") in p.get("skin_types", []):
                score += 10.0
            if concern in ["dandruff", "hair fall", "dry hair", "oily scalp"] and concern.replace(" hair", "").replace(" scalp", "") in p.get("hair_types", []):
                score += 10.0
            if concern == "baby care" and p.get("baby_safe"):
                score += 10.0

            # Benefit & Ingredient matches in structured lists
            for ben in p.get("benefits", []):
                if ben.lower() in concern or concern in ben.lower():
                    score += 6.0
            for ing in p.get("ingredients", []):
                if ing.lower() in message.lower():
                    score += 8.0

        # Identify requested product types in the query
        requested_types = [t for t in ["soap", "shampoo", "serum", "powder", "oil", "butter", "lotion", "cream"] if t in message.lower()]
        
        # --------------------------------------------------
        # STAGE 2: Keyword Description Matching (Secondary Weight)
        # --------------------------------------------------
        if concern:
            concern_words = CONCERN_KEYWORDS.get(concern, [concern])
            for cw in concern_words:
                if cw in name_lower:
                    score += 5.0
                if cw in desc_lower:
                    score += 1.0

        # General generic text keyword alignments (removed product types from exclusion)
        msg_words = set(re.findall(r"\w+", message.lower()))
        msg_words = {w for w in msg_words if w not in ["care", "wellness", "for", "and", "the", "skin", "hair", "have", "i", "do", "you"]}
        
        for word in msg_words:
            if word in name_lower:
                score += 4.0
            if word in p.get("categories", []):
                score += 3.0
            if word in p.get("tags", []):
                score += 3.0
            if word in [ing.lower() for ing in p.get("ingredients", [])]:
                score += 3.0
            if word in desc_lower:
                score += 0.5

        # Strict Product Type Filtering Penalty
        # If the user specifically asked for a type (e.g. "soap"), heavily penalize products that are not that type
        if requested_types and p.get("product_type") not in requested_types:
            continue

        # Only recommend if it meets our strict score threshold
        if score >= 5.0:
            scored_products.append((score, p))

    # Sort descending by score
    scored_products.sort(key=lambda x: x[0], reverse=True)
    top_matches = [item[1] for item in scored_products[:3]]

    prefix = ""
    top_product = top_matches[0] if top_matches else None
    if not top_matches:
        if concern == "diaper rash":
            return "I couldn't find any products specifically for diaper rash in our current catalog.", None
        if concern == "baby care" and not requested_types:
            return "I couldn't find any products specifically designed or labeled for babies in our current catalog.", None
            
        # Fallback to closest match if no products passed the strict threshold, but STILL enforce product type!
        closest_scored = [
            (0.5, p) for p in products 
            if not check_metadata_contradiction(concern or "generic", p)
            and not (requested_types and p.get("product_type") not in requested_types)
        ]
        top_matches = [item[1] for item in closest_scored[:3]]
        top_product = top_matches[0] if top_matches else None
        
        if not top_matches:
            if concern == "baby care":
                return "I couldn't find any products specifically designed or labeled for babies in our current catalog.", None
            return "I couldn't find any products in our catalog matching that concern. Feel free to browse our organic collection!", None
            
        prefix = "I couldn't find a product specifically designed for your concern, but these are the closest matches:\n\n"
    else:
        prefix = "Here are our top recommended products for your concern:\n\n"

    # Format output comparison table
    res = prefix
    res += "| Product | Price | Link |\n"
    res += "| :--- | :--- | :--- |\n"
    
    reasons_list = []
    for p in top_matches:
        try:
            price_val = float(p.get("price", 0))
            price_str = f"₹{int(price_val)}" if price_val.is_integer() else f"₹{price_val:.2f}"
        except Exception:
            price_str = f"₹{p.get('price')}"
            
        res += f"| **{p['name']}** | {price_str} | [View Product]({p['permalink']}) |\n"
        
        # Build explainability bullet point
        explanation = generate_explanation(concern or "generic", p)
        reasons_list.append(f"- **{p['name']}**: {explanation}")

    res += "\n**Why we recommend these:**\n"
    res += "\n".join(reasons_list)
    res += "\n\nWould you like me to add any of these to your cart?"
    return res, top_product
