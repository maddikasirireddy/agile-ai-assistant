import time
import logging
import re
from typing import List, Dict, Any, Tuple, Optional
from services.intent_classifier import extract_entities
from services.search_service import search_products_local
from services.woocommerce_service import wc_service
from services.faq_service import (
    get_shipping_info, 
    get_returns_info, 
    get_payment_info, 
    get_contact_info, 
    get_store_info, 
    lookup_faq_answer
)
from services.recommendation_service import get_product_recommendations, extract_concern
from services.order_service import track_latest_order
from services.gemini_service import run_chat_session, checkout, add_to_cart, remove_from_cart, calculate_total
from services.cart_service import cart_var
from services.session_service import get_session_state, update_session_state, reset_session

logger = logging.getLogger("agile_wellness")


def resolve_clarification(user_text: str, candidates: List[Dict[str, Any]], session_id: str) -> Optional[Dict[str, Any]]:
    """Resolves which product candidate is selected by name or ordinal reference."""
    def normalize_for_clarification(s: str) -> str:
        s = s.lower()
        s = s.replace("&amp;", "and").replace("&", "and")
        s = re.sub(r"[^\w\s]", " ", s)
        return re.sub(r"\s+", " ", s).strip()

    text_norm = normalize_for_clarification(user_text)
    
    logger.info(f"[CLARIFICATION DEBUG] session_id: {session_id}")
    logger.info(f"[CLARIFICATION DEBUG] raw user message: '{user_text}'")
    logger.info(f"[CLARIFICATION DEBUG] normalized user message: '{text_norm}'")
    logger.info(f"[CLARIFICATION DEBUG] clarification_candidates: {[p.get('name') for p in candidates]}")
    
    # 1. Exact match against candidates
    for p in candidates:
        name_norm = normalize_for_clarification(p.get("name", ""))
        logger.info(f"[CLARIFICATION DEBUG] comparing against normalized candidate: '{name_norm}'")
        if text_norm == name_norm:
            logger.info(f"[CLARIFICATION DEBUG] exact match result: TRUE for '{p.get('name')}'")
            return p
            
    # 2. Substring match
    for p in candidates:
        name_norm = normalize_for_clarification(p.get("name", ""))
        if name_norm in text_norm or text_norm in name_norm:
            logger.info(f"[CLARIFICATION DEBUG] exact match result: FALSE, fuzzy match result: TRUE for '{p.get('name')}'")
            return p

    logger.info("[CLARIFICATION DEBUG] exact match result: FALSE, fuzzy match result: FALSE")

    # 3. Ordinal checks
    text = user_text.lower().strip()
    if any(term in text for term in ["first", "1st", "1", "one"]):
        return candidates[0]
    if len(candidates) > 1 and any(term in text for term in ["second", "2nd", "2", "two"]):
        return candidates[1]
    if len(candidates) > 2 and any(term in text for term in ["third", "3rd", "3", "three"]):
        return candidates[2]
    
    return None

class SessionMemory:
    """Retrieves and manages conversation state from the session service."""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.state = get_session_state(session_id)
        
    @property
    def current_product(self) -> Optional[Dict[str, Any]]:
        return self.state["selected_product"]
        
    @current_product.setter
    def current_product(self, val: Optional[Dict[str, Any]]):
        update_session_state(self.session_id, {"selected_product": val})
        
    @property
    def current_concern(self) -> Optional[str]:
        return self.state["user_concern"]
        
    @current_concern.setter
    def current_concern(self, val: Optional[str]):
        update_session_state(self.session_id, {"user_concern": val})
        
    @property
    def current_category(self) -> Optional[str]:
        return self.state.get("current_category")
        
    @current_category.setter
    def current_category(self, val: Optional[str]):
        update_session_state(self.session_id, {"current_category": val})
        
    @property
    def last_clarification_candidates(self) -> List[Dict[str, Any]]:
        return self.state["clarification_candidates"]
        
    @last_clarification_candidates.setter
    def last_clarification_candidates(self, val: List[Dict[str, Any]]):
        update_session_state(self.session_id, {"clarification_candidates": val})

def format_product_detail(intent: str, p: Dict[str, Any]) -> str:
    p_name = p.get("name")
    permalink = p.get("permalink")
    desc = p.get("description", "")
    short_desc = p.get("short_description", "")
    desc_clean = re.sub(r'<[^>]+>', '', desc + " " + short_desc).strip()
    
    try:
        price_val = float(p.get("price", 0))
        price_str = f"₹{int(price_val)}" if price_val.is_integer() else f"₹{price_val:.2f}"
    except Exception:
        price_str = f"₹{p.get('price')}"

def format_product_detail(intent: str, product: Dict[str, Any]) -> str:
    """Extracts the most relevant detail from the product based on intent."""
    p_name = product.get("name", "This product")
    price_str = f"₹{product.get('price', 0)}"
    permalink = product.get("permalink", "")
    desc_clean = re.sub(r'<[^>]+>', '', product.get("description", "") or product.get("short_description", "")).strip()

    if intent == "ingredient_information":
        ingredients = product.get("ingredients", [])
        if ingredients:
            return f"**{p_name}** contains the following ingredients:\n\n" + "\n".join([f"- {i.capitalize()}" for i in ingredients])
        return f"I couldn't find a detailed ingredients list for **{p_name}**. Please view details: [View Product]({permalink})"
        
    elif intent == "product_price":
        return f"The price of **{p_name}** is {price_str}. [View Product]({permalink})"
        
    elif intent == "product_availability":
        status = "In Stock" if product.get("stock_status") == "instock" else "Out of Stock"
        return f"**{p_name}** is currently **{status}**. [View Product]({permalink})"
        
    elif intent == "product_usage":
        usage_match = re.search(r"(?:how to use|usage|apply|directions):\s*([^\.]+)", desc_clean, re.IGNORECASE)
        if usage_match:
            return f"Here is how to use **{p_name}**:\n\n{usage_match.group(0).strip()}.\n\n[View Product Details]({permalink})"
        return f"To use **{p_name}**, please refer to the packaging directions or check online: [View Product Details]({permalink})"
        
    weight_match = re.search(r"\b\d+\s*(?:ml|g|gm|kg|oz|ounce)\b", p_name + " " + desc_clean, re.IGNORECASE)
    weight_str = f"**Size/Weight:** {weight_match.group(0)}\n" if weight_match else ""
    
    benefits = product.get("benefits", [])
    benefits_str = f"**Key Benefits:** {', '.join(benefits[:3])}\n" if benefits else ""
    
    options_match = re.search(r"\((Mango, Strawberry, Chocolate[^\)]*)\)", p_name, re.IGNORECASE)
    variants_str = f"**Available Flavors/Variants:** {options_match.group(1)}\n" if options_match else ""

    summary = f"Here is the detail for **{p_name}**:\n\n"
    summary += f"**Price:** {price_str}\n"
    summary += weight_str
    summary += benefits_str
    summary += variants_str
    if len(desc_clean) > 180:
        desc_clean = desc_clean[:180] + "..."
    if desc_clean:
        summary += f"**Description:** {desc_clean}\n\n"
    summary += f"[View Product Details]({permalink})"
    return summary

def run_hybrid_chat_flow(
    message: str, 
    history: List[Dict[str, Any]], 
    cart: List[Dict[str, Any]],
    customer_id: Optional[int] = None,
    session_id: Optional[str] = None
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Stateful hybrid request orchestrator.
    Minimizes Gemini API usage and guarantees product/FAQ correctness.
    """
    start_time = time.perf_counter()
    cart_var.set(cart)
    
    # 1. Fetch WooCommerce catalog and reconstruct state memory
    products = wc_service.get_products()
    
    if not session_id:
        session_id = f"fallback_{customer_id or 'guest'}"
        
    memory = SessionMemory(session_id)

    # 2. Intent & Entity Extraction
    entities = extract_entities(message)
    intent = entities.get("intent", "unknown")
    logger.info(f"Hybrid Pipeline: Extracted intent '{intent}' for session '{session_id}'")

    # Update dynamic state context parameters
    concern = entities.get("concern")
    if concern:
        memory.current_concern = concern
    category = entities.get("category")
    if category:
        memory.current_category = category

    update_session_state(session_id, {
        "last_user_action": message,
        "shopping_action": intent if intent in ("add_to_cart", "remove_from_cart", "checkout", "buy_now", "quantity_change", "view_cart") else None
    })

    # 3. Product Resolution (Unified local search engine)
    filters = {}
    if entities.get("max_price"): filters["max_price"] = float(entities["max_price"])
    if entities.get("min_price"): filters["min_price"] = float(entities["min_price"])
    
    # We want to search based on product or ingredient if specified
    search_query = message
    if entities.get("product"):
        search_query = entities["product"]
    elif entities.get("ingredient"):
        search_query = entities["ingredient"]
    elif entities.get("category"):
        search_query = entities["category"]
        
    scored_matches = search_products_local(products, search_query, filters)
    
    # Separate into high-confidence (exact) matches and close matches
    exact_match_threshold = 80.0
    close_match_threshold = 20.0
    
    exact_matches = [p for p in scored_matches if p.get("_search_score", 0) >= exact_match_threshold]
    close_matches = [p for p in scored_matches if p.get("_search_score", 0) >= close_match_threshold]
    
    # If there are exact matches, use them to avoid prompting clarification among weak matches
    matching_products = exact_matches if exact_matches else close_matches
    
    target_product = None
    
    # Auto-resolve if the top match is significantly better than the rest
    if len(matching_products) > 1:
        top_score = matching_products[0].get("_search_score", 0)
        second_score = matching_products[1].get("_search_score", 0)
        if top_score > second_score + 100 or top_score >= second_score * 1.5:
            matching_products = [matching_products[0]]

    # Check if we are resolving a pending clarification
    if memory.last_clarification_candidates:
        resolved = resolve_clarification(message, memory.last_clarification_candidates, session_id)
        if resolved:
            logger.info(f"Hybrid Pipeline: Resolved clarification list to '{resolved['name']}'")
            target_product = resolved
            memory.current_product = resolved
            
            # Resume original query intent
            intent = memory.state["pending_intent"] or "product_information"
            message = memory.state["original_request"] or message
            
            # Clear pending clarification state
            update_session_state(session_id, {
                "clarification_candidates": [],
                "pending_intent": None,
                "original_request": None
            })

    # Resolve matched target product
    if not target_product:
        if len(matching_products) == 1:
            target_product = matching_products[0]
            memory.current_product = target_product
            if intent == "unknown":
                intent = "product_information"
        elif len(matching_products) > 1:
            if intent == "unknown":
                intent = "product_information"
            # Check if matching intent is product question/action
            if intent in (
                "product_detail", "product_search", "add_to_cart", "remove_from_cart"
            ):
                update_session_state(session_id, {
                    "clarification_candidates": matching_products,
                    "pending_intent": intent,
                    "original_request": message
                })
                reply = "Did you mean one of these products?\n\n"
                reply += "\n".join([f"- **{p.get('name')}**" for p in matching_products])
                reply += "\n\nPlease specify which product you are referring to!"
                
                # Log state details
                logger.info(
                    f"SESSION ID: {session_id} | "
                    f"STATE: {memory.state} | "
                    f"PENDING INTENT: {intent} | "
                    f"SELECTED PRODUCT: None | "
                    f"CLARIFICATION STATUS: True"
                )
                return reply, cart_var.get()
        else:
            # Pronoun/Context reference fallback
            is_explicit_pronoun = any(term in message.lower() for term in ["it", "that", "this", "those", "them"])
            if (
                intent in (
                    "product_detail", "product_search", "add_to_cart", 
                    "remove_from_cart"
                ) or
                is_explicit_pronoun or
                any(term in message.lower() for term in ["soap", "shampoo", "powder", "oil", "butter", "lotion", "serum"])
            ):
                # Context overrides: Do not use active product if the user explicitly raises a NEW concern!
                # E.g. "What can I use for baby diaper rash?" (concern="diaper rash")
                # But if they ask "Is it good for acne?", there is a pronoun ("it"), so we KEEP target_product.
                if concern and not is_explicit_pronoun:
                    target_product = None
                else:
                    target_product = memory.current_product

    # Log state details
    logger.info(
        f"SESSION ID: {session_id} | "
        f"STATE: {memory.state} | "
        f"PENDING INTENT: {memory.state['pending_intent']} | "
        f"SELECTED PRODUCT: {target_product.get('name') if target_product else 'None'} | "
        f"CLARIFICATION STATUS: {len(memory.last_clarification_candidates) > 0}"
    )

    reply = None
    source = "Local Engine"
    gemini_called = False

    try:
        # 4. Routing Flow (Priority Based)
        
        # 1. Cart Actions
        if intent == "add_to_cart":
            if target_product:
                qty = entities.get("quantity") or 1
                reply = add_to_cart(target_product.get("id"), qty)
                source = "Local Cart Add Action"
            else:
                reply = "Which product would you like to add to your cart?"
        
        elif intent == "remove_from_cart":
            if target_product:
                reply = remove_from_cart(target_product.get("id"))
                source = "Local Cart Remove Action"
            else:
                reply = "Which product would you like to remove from your cart?"
                
        elif intent == "view_cart":
            reply = calculate_total()
            source = "Local Cart View Action"

        elif intent in ("checkout", "buy_now"):
            if intent == "buy_now" and target_product:
                qty = entities.get("quantity") or 1
                add_to_cart(target_product.get("id"), qty)
                reply = checkout()
                source = "Local Buy Now Action"
            else:
                reply = checkout()
                source = "Local Checkout Action"

        # 2. Order Actions
        elif intent in ("order_status", "track_order", "reorder", "order_history", "latest_order"):
            if customer_id is None:
                reply = "Please log in to view your orders."
            else:
                reply = track_latest_order(customer_id)
            source = "WooCommerce Order Lookup"
            
        # 3. Recommendations
        elif intent == "recommendation":
            rec_query = entities.get("concern") or message
            reply, top_product = get_product_recommendations(rec_query)
            if top_product:
                target_product = top_product
                memory.current_product = top_product
            source = "WooCommerce Product Recommendation"

        # 4. Filtered Browsing
        elif intent == "product_browsing":
            if matching_products:
                reply = "Here are the top products that match your request:\n\n"
                for p in matching_products[:5]:
                    reply += f"- **{p.get('name')}** (₹{p.get('price', 0)})\n"
                source = "Local Browsing Action"
            else:
                reply = "I couldn't find any products matching those criteria."
                source = "Local Browsing Action"

        # 5. Product Detail
        elif intent == "product_detail":
            if target_product:
                # Default to product_information or ingredient based on user query
                sub_intent = "ingredient_information" if entities.get("ingredient") else "product_information"
                reply = format_product_detail(sub_intent, target_product)
                source = "WooCommerce Product Details"
            else:
                reply = "Which product would you like details for?"
                
        elif intent == "product_search":
            if target_product:
                reply = format_product_detail("product_information", target_product)
                source = "WooCommerce Product Search"
            else:
                reply = "I couldn't find that product."

        # Greetings & FAQS
        elif intent == "greeting":
            reply = "Hello! Welcome to Agile Wellness. I am your shopping and wellness assistant. How can I help you today?"
        elif intent == "goodbye":
            reply = "Thank you for visiting Agile Wellness. Have a beautiful, healthy day ahead! Goodbye!"

        # 6. Gemini Fallback
        if reply is None:
            logger.info("Local engine could not resolve query. Delegating to Gemini fallback...")
            reply, updated_cart = run_chat_session(message, history, cart_var.get(), customer_id)
            gemini_called = True
            source = "Gemini AI Fallback"
        else:
            updated_cart = cart_var.get()

        update_session_state(session_id, {"last_bot_action": reply})

        elapsed = time.perf_counter() - start_time
        logger.info(
            f"Request resolved in {elapsed:.3f}s | Source: {source} | "
            f"Intent: {intent} | Target: {target_product.get('name') if target_product else 'None'} | "
            f"Gemini Called: {gemini_called}"
        )
        return reply, updated_cart

    except Exception as e:
        elapsed = time.perf_counter() - start_time
        logger.error(f"Error resolving hybrid flow after {elapsed:.3f}s: {e}")
        return (
            "I'm sorry, I couldn't find a reliable answer for that. Please contact Agile Wellness for further assistance.",
            cart_var.get()
        )

# Helper functions for clarification tracking
def role_was_clarification(history: List[Dict[str, Any]]) -> bool:
    """Returns True if the last model response was a clarification question."""
    if not history:
        return False
    # Check last response from model (AI or model role)
    for msg in reversed(history):
        if msg.get("role") in ("model", "ai"):
            return "did you mean one of these products?" in msg.get("text", "").lower()
    return False

def find_original_query_intent(history: List[Dict[str, Any]]) -> str:
    """Traverses history backwards to locate the original query before clarification."""
    for msg in reversed(history):
        if msg.get("role") == "user":
            txt = msg.get("text", "")
            entities = extract_entities(txt)
            return entities.get("intent", "product_detail")
    return "product_detail"
