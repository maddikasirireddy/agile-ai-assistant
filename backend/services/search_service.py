import re
import difflib
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger("agile_wellness")

def normalize_text(text: str) -> str:
    """Clean HTML tags, lowercase, and remove non-alphanumeric characters."""
    if not text:
        return ""
    # Strip HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Lowercase and keep alphanumeric characters/spaces
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return " ".join(text.split())

def calculate_word_similarity(word1: str, word2: str) -> float:
    """Calculate fuzzy ratio between two words."""
    return difflib.SequenceMatcher(None, word1, word2).ratio()

def search_products_local(products: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    """
    Scored product search based on:
    - Name exact/substring matches
    - Categories & tags
    - Short description & description
    - Fuzzy matching on terms
    - Concern/synonym mapping
    """
    if not query or not products:
        return []

    norm_query = normalize_text(query)
    query_words = [w for w in norm_query.split() if len(w) > 2]
    if not query_words:
        query_words = norm_query.split()
    if not query_words:
        return []

    # Concern mapping to boost products targeting specific ailments or terms
    concern_map = {
        "hair fall": ["bhringraj", "amla", "shampoo", "conditioner", "onion"],
        "hair growth": ["bhringraj", "amla", "shampoo", "conditioner", "onion"],
        "hair loss": ["bhringraj", "amla", "shampoo", "conditioner", "onion"],
        "dandruff": ["onion", "shampoo", "anti-dandruff"],
        "dry hair": ["damage repair", "green apple", "shampoo", "conditioner"],
        "oily skin": ["herbal blast", "face wash", "neem", "multani mitti", "charcoal"],
        "acne": ["anti-acne", "serum", "neem", "charcoal"],
        "pimples": ["anti-acne", "serum", "neem", "charcoal"],
        "anti-aging": ["anti-aging", "serum", "deaging", "rose"],
        "aging": ["anti-aging", "serum", "deaging", "rose"],
        "wrinkles": ["anti-aging", "serum", "deaging"],
        "dry skin": ["rose", "avocado", "lip butter", "moisturizing", "lotion"],
        "glow": ["orange peel", "multani mitti", "rose", "gulab"],
        "tan": ["orange peel", "multani mitti"],
    }

    scored_products: List[Tuple[Dict[str, Any], float]] = []

    for product in products:
        score = 0.0
        
        name = product.get("name", "")
        short_desc = product.get("short_description", "")
        desc = product.get("description", "")
        
        categories = [c["name"] if isinstance(c, dict) else str(c) for c in product.get("categories", [])]
        tags = [t["name"] if isinstance(t, dict) else str(t) for t in product.get("tags", [])]
        
        norm_name = normalize_text(name)
        norm_short_desc = normalize_text(short_desc)
        norm_desc = normalize_text(desc)
        
        norm_categories = [normalize_text(c) for c in categories]
        norm_tags = [normalize_text(t) for t in tags]

        # 1. Exact phrase match in product name (highest priority)
        if norm_query in norm_name:
            score += 100.0
            
        # 2. Match in categories or tags
        for norm_cat in norm_categories:
            if norm_query in norm_cat:
                score += 50.0
        for norm_tag in norm_tags:
            if norm_query in norm_tag:
                score += 50.0

        # 3. Individual query word scoring
        for q_word in query_words:
            # Word match in name
            if q_word in norm_name:
                score += 30.0
            else:
                # Fuzzy match name words
                for name_word in norm_name.split():
                    if calculate_word_similarity(q_word, name_word) > 0.8:
                        score += 20.0
            
            # Word match in categories
            for norm_cat in norm_categories:
                if q_word in norm_cat:
                    score += 15.0
                else:
                    for cat_word in norm_cat.split():
                        if calculate_word_similarity(q_word, cat_word) > 0.8:
                            score += 10.0
                            
            # Word match in tags
            for norm_tag in norm_tags:
                if q_word in norm_tag:
                    score += 15.0
                else:
                    for tag_word in norm_tag.split():
                        if calculate_word_similarity(q_word, tag_word) > 0.8:
                            score += 10.0

            # Match in description and short description
            if q_word in norm_short_desc:
                score += 8.0
            if q_word in norm_desc:
                score += 4.0

        # 4. Concern mapping boosts
        for concern, keywords in concern_map.items():
            if concern in norm_query:
                # If this concern is found in user query, boost products matching concern keywords
                combined_details = f"{norm_name} {norm_short_desc} {' '.join(norm_categories)} {' '.join(norm_tags)}"
                for kw in keywords:
                    if kw in combined_details:
                        score += 40.0

        if score > 0:
            scored_products.append((product, score))

    # Sort by score descending
    scored_products.sort(key=lambda x: x[1], reverse=True)
    
    logger.info(f"Local search for query '{query}' yielded {len(scored_products)} matches.")
    return [p for p, _ in scored_products]
