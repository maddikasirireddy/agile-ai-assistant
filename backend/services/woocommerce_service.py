import os
import time
import logging
import re
from typing import List, Dict, Any, Optional
from woocommerce import API
from services.cache_service import global_cache

logger = logging.getLogger("agile_wellness")

class WooCommerceService:
    """Service to handle communication with WooCommerce API with caching and attribute enrichment."""
    
    def __init__(self):
        self.url = os.getenv("WC_URL")
        self.consumer_key = os.getenv("WC_CONSUMER_KEY")
        self.consumer_secret = os.getenv("WC_CONSUMER_SECRET")
        self.timeout = int(os.getenv("WC_TIMEOUT", 30))
        
        if not all([self.url, self.consumer_key, self.consumer_secret]):
            raise RuntimeError(
                "WooCommerce credentials not found in environment variables. "
                "Ensure WC_URL, WC_CONSUMER_KEY, and WC_CONSUMER_SECRET are defined."
            )
            
        self.api = API(
            url=self.url,
            consumer_key=self.consumer_key,
            consumer_secret=self.consumer_secret,
            version="wc/v3",
            timeout=self.timeout
        )

    def get_products(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Retrieve products from the TTL cache or call the WooCommerce API.
        Enriches product records with metadata extracted from attributes and text descriptions.
        """
        cache_key = "wc_products_catalog"
        
        if not force_refresh:
            cached_data = global_cache.get(cache_key)
            if cached_data is not None:
                logger.info("Serving products from local TTL cache.")
                return cached_data

        logger.info("Cache expired or empty. Querying WooCommerce API for products...")
        start_time = time.perf_counter()
        try:
            page = 1
            all_raw_products = []
            while True:
                response = self.api.get("products", params={"per_page": 100, "status": "publish", "page": page})
                
                if response.status_code not in (200, 201):
                    logger.error(
                        f"WooCommerce returned error code {response.status_code} during products fetch page {page}: {response.text}"
                    )
                    break
                    
                products_page = response.json()
                if not products_page:
                    break
                    
                all_raw_products.extend(products_page)
                
                total_pages = int(response.headers.get("X-WP-TotalPages", 1))
                if page >= total_pages:
                    break
                    
                page += 1
                
            elapsed = time.perf_counter() - start_time
            logger.info(f"WooCommerce API GET /products fetched {len(all_raw_products)} items across {page} pages in {elapsed:.2f}s")
            
            if all_raw_products:
                enriched_products = [self._enrich_product(p) for p in all_raw_products]
                global_cache.set(cache_key, enriched_products)
                logger.info(f"Successfully cached {len(enriched_products)} enriched products.")
                return enriched_products
            else:
                stale = global_cache.get_stale(cache_key)
                if stale is not None:
                    logger.warning("Falling back to stale products cache.")
                    return stale
                return []
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(f"WooCommerce products fetch failed with exception after {elapsed:.2f}s: {str(e)}")
            stale = global_cache.get_stale(cache_key)
            if stale is not None:
                logger.warning("Falling back to stale products cache after exception.")
                return stale
            return []

    def _enrich_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and normalize product attributes and infer missing ones from descriptions.
        Provides clean, semantic properties: skin_types, hair_types, concerns, ingredients, 
        benefits, product_type, body_area, baby_safe, recommended_for, and avoid_for.
        """
        pid = product.get("id")
        name = product.get("name", "")
        desc = product.get("description", "")
        short_desc = product.get("short_description", "")
        combined_text = f"{name} {desc} {short_desc}".lower()
        combined_text_clean = re.sub(r'<[^>]+>', '', combined_text)

        # 1. Map WooCommerce attributes
        wc_attrs = {a["name"].lower(): [o.lower() for o in a.get("options", [])] for a in product.get("attributes", [])}
        
        # 2. Extract ingredients
        ingredients = []
        for key, opts in wc_attrs.items():
            if any(term in key for term in ["ingredient", "content", "formula"]):
                ingredients.extend(opts)
        if not ingredients:
            ing_match = re.search(r"ingredients?:\s*([^\.]+)", combined_text_clean)
            if ing_match:
                ingredients = [i.strip() for i in ing_match.group(1).split(",") if i.strip()]
            else:
                common_ingredients = ["neem", "amla", "bhringraj", "shikakai", "onion", "rose", "saffron", "lavender", "coconut", "aloe", "sandalwood", "turmeric", "almond", "shea butter", "tea tree", "charcoal", "multani mitti"]
                for ing in common_ingredients:
                    if ing in combined_text_clean:
                        ingredients.append(ing)

        # 3. Extract benefits
        benefits = []
        for key, opts in wc_attrs.items():
            if any(term in key for term in ["benefit", "use for", "feature"]):
                benefits.extend(opts)
        if not benefits:
            common_benefits = ["hair fall", "dandruff", "acne", "pimples", "dry skin", "oily skin", "brightening", "glowing", "anti-aging", "wrinkles", "moisturizing", "hydrating", "anti-bacterial", "soothing"]
            for ben in common_benefits:
                if ben in combined_text_clean:
                    benefits.append(ben)

        # 4. Skin type suitability
        skin_types = []
        for key, opts in wc_attrs.items():
            if "skin" in key:
                skin_types.extend(opts)
        if not skin_types:
            for st in ["dry skin", "oily skin", "sensitive skin", "normal skin", "combination skin"]:
                if st in combined_text_clean:
                    skin_types.append(st.replace(" skin", ""))
            if "acne" in combined_text_clean or "pimple" in combined_text_clean:
                skin_types.append("oily")
                skin_types.append("combination")
                skin_types.append("acne-prone")

        # 5. Hair type suitability
        hair_types = []
        for key, opts in wc_attrs.items():
            if "hair" in key:
                hair_types.extend(opts)
        if not hair_types:
            for ht in ["dry hair", "oily hair", "dandruff", "hair fall", "damaged hair"]:
                if ht in combined_text_clean:
                    hair_types.append(ht.replace(" hair", ""))
            if any(term in combined_text_clean for term in ["shampoo", "scalp", "bhringraj", "shikakai"]):
                if "dry" in combined_text_clean:
                    hair_types.append("dry")
                if "dandruff" in combined_text_clean:
                    hair_types.append("dandruff")

        # 6. Baby safe suitability
        baby_safe = False
        for key, opts in wc_attrs.items():
            if "baby" in key:
                baby_safe = True
        if not baby_safe:
            if any(term in combined_text_clean for term in ["baby", "infant", "newborn", "kids"]):
                baby_safe = True
        if not baby_safe:
            if any("baby" in c.get("name", "").lower() for c in product.get("categories", [])):
                baby_safe = True

        # 7. Product type classification
        product_type = "general"
        for t in ["soap", "shampoo", "serum", "powder", "oil", "butter", "lotion"]:
            if t in name.lower() or t in combined_text_clean:
                product_type = t
                break

        # 8. Body area classification
        body_area = "body"
        if product_type in ["shampoo"] or any(t in combined_text_clean for t in ["hair", "scalp", "dandruff"]):
            body_area = "hair"
        elif "lip" in name.lower() or "lip" in combined_text_clean:
            body_area = "lips"
        elif any(t in name.lower() or t in combined_text_clean for t in ["face", "acne", "pimple", "serum", "mitti"]):
            body_area = "face"

        # 9. Concerns list
        concerns = []
        concern_map = {
            "acne": ["acne", "pimple", "pimples", "blemish", "blemishes"],
            "dry skin": ["dry skin", "dryness", "dehydrated"],
            "oily skin": ["oily skin", "greasy skin", "excess oil", "sebum"],
            "sensitive skin": ["sensitive skin", "sensitive", "irritation"],
            "pigmentation": ["pigmentation", "dark spot", "spots", "uneven tone"],
            "tan removal": ["tan", "detan", "de-tan", "tan removal"],
            "hair fall": ["hair fall", "thinning", "hair loss"],
            "dandruff": ["dandruff", "flaky scalp"],
            "dry hair": ["dry hair", "frizzy hair"],
            "oily scalp": ["oily scalp", "greasy hair"]
        }
        for con, syns in concern_map.items():
            if any(s in combined_text_clean for s in syns):
                concerns.append(con)

        # 10. Recommended For & Avoid For lists
        recommended_for = []
        recommended_for.extend(skin_types)
        recommended_for.extend(hair_types)
        recommended_for.extend(concerns)
        if baby_safe:
            recommended_for.append("baby care")

        avoid_for = []
        if "oily" in skin_types and "dry" not in skin_types:
            avoid_for.append("very dry skin")
        if "dry" in skin_types and "oily" not in skin_types:
            avoid_for.append("oily skin")
        if "dandruff" in hair_types or "oily scalp" in concerns:
            avoid_for.append("dry scalp")
        if not baby_safe and any(term in name.lower() or term in combined_text_clean for term in ["acne", "pimple", "anti-aging", "anti-dandruff"]):
            avoid_for.append("baby skin")

        categories = [c["name"].lower() for c in product.get("categories", [])]
        tags = [t["name"].lower() for t in product.get("tags", [])]

        return {
            "id": product.get("id"),
            "name": product.get("name"),
            "slug": product.get("slug"),
            "price": product.get("price"),
            "sale_price": product.get("sale_price"),
            "stock_status": product.get("stock_status", "instock"),
            "description": desc,
            "short_description": short_desc,
            "permalink": product.get("permalink"),
            "images": [img.get("src") for img in product.get("images", []) if img.get("src")],
            "categories": categories,
            "tags": tags,
            "skin_types": list(set(skin_types)),
            "hair_types": list(set(hair_types)),
            "concerns": list(set(concerns)),
            "ingredients": list(set(ingredients)),
            "benefits": list(set(benefits)),
            "product_type": product_type,
            "body_area": body_area,
            "baby_safe": baby_safe,
            "recommended_for": list(set(recommended_for)),
            "avoid_for": list(set(avoid_for))
        }

# Shared singleton instance
wc_service = WooCommerceService()
