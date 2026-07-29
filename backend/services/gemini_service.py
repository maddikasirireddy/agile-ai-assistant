import os
import time
import logging
import re
import json
from typing import List, Dict, Any, Tuple, Optional
import google.generativeai as genai
from utils.prompts import SYSTEM_INSTRUCTION
from services.woocommerce_service import wc_service
from services.search_service import search_products_local
from services.cart_service import cart_var, add_to_cart_logic, remove_from_cart_logic, calculate_total_logic
from services.order_service import (
    track_order_logic, 
    track_latest_order, 
    list_orders, 
    order_details, 
    reorder_last_order
)

logger = logging.getLogger("agile_wellness")

# ----------------------------------------------------
# Gemini Tool Declarations (Exposed to Model)
# ----------------------------------------------------

def search_product(query: str) -> str:
    """
    Search the WooCommerce store catalog for products matching a given query, keyword, category, tag, or description.
    Use this tool when the customer wants to find products (e.g., 'Do you have neem soaps?').
    
    Args:
        query: The search term (e.g. 'soap', 'shampoo', 'mitti').
    """
    try:
        products = wc_service.get_products()
        matches = search_products_local(products, query)
        
        if not matches:
            return f"No products found matching '{query}'."

        result = "Matching products found in catalog:\n"
        for p in matches:
            price = p.get('price', 'N/A')
            images = p.get("images", [])
            img_src = ""
            if images:
                first_img = images[0]
                img_src = first_img.get("src") if isinstance(first_img, dict) else str(first_img)
            desc = p.get('short_description') or p.get('description', '')
            desc_clean = re.sub(r'<[^>]+>', '', desc).strip()
            if len(desc_clean) > 120:
                desc_clean = desc_clean[:120] + "..."
                
            # Format price cleanly without decimals if whole
            try:
                price_val = float(price)
                price_str = f"{int(price_val)}" if price_val.is_integer() else f"{price_val:.2f}"
            except Exception:
                price_str = price

            result += f"- **{p.get('name')}** | Price: ₹{price_str}\n"
            if desc_clean:
                result += f"  *Description*: {desc_clean}\n"
            result += f"  *Link*: [View Product]({p.get('permalink')})\n"
            if img_src:
                result += f"  *Image*: {img_src}\n"
        return result
    except Exception as e:
        logger.error(f"Error in search_product tool: {e}")
        return f"Error searching products: {str(e)}"


def recommend_product(query: str) -> str:
    """
    Recommend products from the catalog based on skin/hair concern, category, or customer preference.
    Use this when the customer asks for recommendations (e.g., 'I need something for dry hair').
    
    Args:
        query: The wellness concern or product category (e.g. 'hair fall', 'dry skin', 'face wash').
    """
    return search_product(query)


def add_to_cart(product_id: int, quantity: int = 1) -> str:
    """
    Add a product from the catalog to the customer's shopping cart.
    Always search for the product first using search_product to get the correct product ID and price.
    
    Args:
        product_id: The unique ID of the product to add.
        quantity: The quantity to add (defaults to 1).
    """
    current_cart = cart_var.get()
    products_list = wc_service.get_products()
    new_cart, message = add_to_cart_logic(current_cart, product_id, quantity, products_list)
    cart_var.set(new_cart)
    return message


def remove_from_cart(product_id: int) -> str:
    """
    Remove a product from the customer's shopping cart using its product ID.
    
    Args:
        product_id: The unique ID of the product to remove.
    """
    current_cart = cart_var.get()
    new_cart, message = remove_from_cart_logic(current_cart, product_id)
    cart_var.set(new_cart)
    return message


def calculate_total() -> str:
    """
    Calculate the total cost of the shopping cart and return a summary of the items currently in the cart.
    Use this when the user asks to see their cart, view their cart, or asks for the total price.
    """
    current_cart = cart_var.get()
    return calculate_total_logic(current_cart)


def track_order(order_id: int) -> str:
    """
    Track the shipping and payment status of a customer's order using the WooCommerce order ID.
    Ask the customer for their order ID if they have not provided it.
    
    Args:
        order_id: The numeric ID of the order to track.
    """
    return track_order_logic(order_id)


def checkout() -> str:
    """Generate a checkout link and instructions for the customer to purchase the items in their cart."""
    current_cart = cart_var.get()
    if not current_cart:
        return "Your cart is empty. Please add some products to your cart before checking out."
        
    first_item = current_cart[0]
    checkout_url = f"https://agilewellness.in/checkout/?add-to-cart={first_item['product_id']}&quantity={first_item['quantity']}"
    
    result = "I've prepared your checkout link!\n\n"
    if len(current_cart) == 1:
        result += f"Click here to checkout with your {first_item['name']}: [Proceed to Checkout]({checkout_url})\n"
    else:
        result += f"Click here to checkout with your items starting with {first_item['name']}: [Proceed to Checkout]({checkout_url})\n\n"
        result += "Note: Because store links add one item at a time, this link adds the first item. You can click 'Checkout' in the cart panel to proceed directly!"
        
    return result

# ----------------------------------------------------
# Gemini Configuration & Session Handler
# ----------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY not found in environment variables.")
else:
    genai.configure(api_key=GEMINI_API_KEY)

# Instantiate the Generative Model
model = None
if GEMINI_API_KEY:
    try:
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            system_instruction=SYSTEM_INSTRUCTION,
            tools=[
                search_product, 
                recommend_product, 
                add_to_cart, 
                remove_from_cart, 
                calculate_total, 
                track_order, 
                checkout
            ]
        )
    except Exception as e:
        logger.error(f"Failed to initialize Gemini Model: {e}")


def run_chat_session(
    message: str, 
    history: List[Dict[str, Any]], 
    cart: List[Dict[str, Any]],
    customer_id: Optional[int] = None
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Invokes Gemini to handle open-ended conversations.
    Provides uniform clean error fallback responses on failure, timeouts, or quota limits.
    """
    cart_var.set(cart)
    
    if not model:
        logger.warning("Gemini model not initialized. Returning fallback response.")
        return "I'm sorry, I couldn't find a reliable answer for that. Please contact Agile Wellness for further assistance.", cart_var.get()

    # Convert history
    gemini_history = []
    for msg in history:
        role = "user" if msg.get("role") == "user" else "model"
        gemini_history.append({
            "role": role,
            "parts": [{"text": msg.get("text", "")}]
        })

    # Start chat and generate response
    start_time = time.perf_counter()
    try:
        session = model.start_chat(history=gemini_history, enable_automatic_function_calling=True)
        response = session.send_message(message, request_options={"timeout": 12.0})
        
        elapsed = time.perf_counter() - start_time
        logger.info(f"Gemini API call completed in {elapsed:.2f}s")
        return response.text, cart_var.get()

    except Exception as e:
        elapsed = time.perf_counter() - start_time
        logger.error(f"Gemini execution failed after {elapsed:.2f}s: {e}")
        # Clean fallback message to block stack traces and warn user uniformly
        return "I'm sorry, I couldn't find a reliable answer for that. Please contact Agile Wellness for further assistance.", cart_var.get()
