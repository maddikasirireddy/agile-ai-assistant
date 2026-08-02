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
    # Simple singularization for common e-commerce search terms
    words = []
    for w in text.split():
        if w.endswith('s') and len(w) > 3 and not w.endswith('ss'):
            words.append(w[:-1])
        else:
            words.append(w)
    return " ".join(words)

def calculate_word_similarity(word1: str, word2: str) -> float:
    """Calculate fuzzy ratio between two words."""
    return difflib.SequenceMatcher(None, word1, word2).ratio()

def search_products_local(products: List[Dict[str, Any]], query: str, filters: dict = None) -> List[Dict[str, Any]]:
    """
    Scored product search based on:
    - Name exact/substring matches
    - Categories & tags
    - Short description & description
    - Enriched properties (ingredients, skin types, hair types)
    - Fuzzy matching on terms and reordered words
    - Concern/synonym mapping
    
    Returns a list of matching product dictionaries, sorted by relevance score.
    The score is embedded in the dict as '_search_score'.
    """
    if not query or not products:
        return []

    norm_query = normalize_text(query)
    stop_words = {
        "i", "want", "something", "with", "show", "me", "products", "items", 
        "under", "below", "less", "than", "for", "a", "the", "and", "my",
        "to", "cart", "add", "buy", "get", "purchase", "in", "from", "into",
        "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"
    }
    
    # Strip stop words, digits, and basic plurals (s)
    query_words = []
    for w in norm_query.split():
        if w not in stop_words and not w.isdigit():
            if w.endswith('s') and len(w) > 3 and not w.endswith('ss'):
                query_words.append(w[:-1])
            else:
                query_words.append(w)
                
    if not query_words:
        query_words = norm_query.split()
    if not query_words:
        return []
        
    query_words_set = set(query_words)

    # Concern mapping to boost products targeting specific ailments or terms
    concern_map = {
        "hair fall": ["bhringraj", "amla", "shampoo", "conditioner", "onion"],
        "hair growth": ["bhringraj", "amla", "shampoo", "conditioner", "onion"],
        "hair loss": ["bhringraj", "amla", "shampoo", "conditioner", "onion"],
        "dandruff": ["onion", "shampoo", "anti dandruff"],
        "dry hair": ["damage repair", "green apple", "shampoo", "conditioner"],
        "oily skin": ["herbal blast", "face wash", "neem", "multani mitti", "charcoal"],
        "acne": ["anti acne", "serum", "neem", "charcoal"],
        "pimple": ["anti acne", "serum", "neem", "charcoal"],
        "anti aging": ["anti aging", "serum", "deaging", "rose"],
        "aging": ["anti aging", "serum", "deaging", "rose"],
        "wrinkle": ["anti aging", "serum", "deaging"],
        "dry skin": ["rose", "avocado", "lip butter", "moisturizing", "lotion"],
        "glow": ["orange peel", "multani mitti", "rose", "gulab"],
        "tan": ["orange peel", "multani mitti"],
        "crack lip": ["lip butter", "lip balm"],
        "baby": ["baby"],
        "skincare": ["serum", "face wash", "soap", "moisturizing", "butter", "lotion", "powder"]
    }

    scored_products: List[Dict[str, Any]] = []

    for product in products:
        if filters and 'max_price' in filters:
            try:
                price = float(product.get("price", 0) or 0)
                if price > filters['max_price']:
                    continue
            except ValueError:
                pass
                
        score = 0.0
        
        name = product.get("name", "")
        short_desc = product.get("short_description", "")
        desc = product.get("description", "")
        
        # WooCommerce enriched format uses lists of strings for these
        categories = [str(c) for c in product.get("categories", [])]
        tags = [str(t) for t in product.get("tags", [])]
        ingredients = [str(i) for i in product.get("ingredients", [])]
        skin_types = [str(s) for s in product.get("skin_types", [])]
        hair_types = [str(h) for h in product.get("hair_types", [])]
        
        norm_name = normalize_text(name)
        norm_short_desc = normalize_text(short_desc)
        norm_desc = normalize_text(desc)
        
        norm_categories = [normalize_text(c) for c in categories]
        norm_tags = [normalize_text(t) for t in tags]
        norm_ingredients = [normalize_text(i) for i in ingredients]
        norm_skin = [normalize_text(s) for s in skin_types]
        norm_hair = [normalize_text(h) for h in hair_types]
        
        name_words = set(norm_name.split())

        # 1. Exact phrase match in product name (highest priority)
        if norm_query in norm_name:
            score += 100.0
            
        # 1b. All query words present in name (handles reordered words like "mango lip butter" in "lip butter mango flavor")
        if query_words_set and query_words_set.issubset(name_words):
            score += 80.0
            
        # 2. Match in categories or tags
        for norm_cat in norm_categories:
            if norm_query in norm_cat:
                score += 50.0
        for norm_tag in norm_tags:
            if norm_query in norm_tag:
                score += 50.0
                
        # 2b. Match in enriched data
        for norm_ing in norm_ingredients:
            if norm_query in norm_ing:
                score += 40.0
        for ns in norm_skin:
            if norm_query in ns:
                score += 30.0
        for nh in norm_hair:
            if norm_query in nh:
                score += 30.0

        # 3. Individual query word scoring (Fuzzy & Substring)
        for q_word in query_words:
            if len(q_word) < 3:
                continue
                
            # Word match in name
            if q_word in norm_name:
                score += 30.0
            else:
                # Fuzzy match name words
                for name_word in name_words:
                    if calculate_word_similarity(q_word, name_word) > 0.8:
                        score += 20.0
            
            # Word match in categories/tags/enriched
            combined_fields = norm_categories + norm_tags + norm_ingredients + norm_skin + norm_hair
            for field in combined_fields:
                if q_word == field or f" {q_word} " in f" {field} ":
                    # Massive boost for EXACT ingredient/tag match
                    score += 60.0
                elif q_word in field:
                    score += 15.0
                else:
                    for field_word in field.split():
                        if calculate_word_similarity(q_word, field_word) > 0.85:
                            # Reduced fuzzy weight so exact matches rank higher
                            score += 5.0

            # Match in description
            if q_word in norm_short_desc:
                score += 8.0
            if q_word in norm_desc:
                score += 4.0

        # 4. Concern mapping boosts
        for concern, keywords in concern_map.items():
            if concern in norm_query:
                combined_details = f"{norm_name} {norm_short_desc} {' '.join(norm_categories)} {' '.join(norm_tags)}"
                for kw in keywords:
                    if kw in combined_details:
                        score += 40.0

        if score > 0:
            p_copy = dict(product)
            p_copy["_search_score"] = score
            scored_products.append(p_copy)

    # Sort by score descending
    scored_products.sort(key=lambda x: x["_search_score"], reverse=True)
    
    logger.info(f"Local search for query '{query}' yielded {len(scored_products)} matches.")
    return scored_products
