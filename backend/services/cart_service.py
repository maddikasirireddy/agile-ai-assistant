import logging
from contextvars import ContextVar
from typing import List, Dict, Any, Tuple
from services.woocommerce_service import wc_service

logger = logging.getLogger("agile_wellness")

# ContextVar for thread-local cart state synchronization with Gemini tools
cart_var: ContextVar[List[Dict[str, Any]]] = ContextVar("cart_var", default=[])


def add_to_cart_logic(
    cart: List[Dict[str, Any]], 
    product_id: int, 
    quantity: int, 
    products_list: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Stateless cart manipulation: Add or update a product in the cart.
    Verifies the product against the local cached product list, or queries WooCommerce as fallback.
    """
    try:
        product_id = int(product_id)
        quantity = int(quantity)
    except (ValueError, TypeError):
        return cart, f"Invalid product ID ({product_id}) or quantity ({quantity})."

    # The quantity parameter represents the change/delta. 
    # Negative values are allowed to decrement quantity.

    # 1. Search in local product list
    product = None
    for p in products_list:
        if p.get("id") == product_id:
            product = p
            break

    # 2. Fallback to WooCommerce API directly if not found in cache
    if not product:
        logger.info(f"Product ID {product_id} not in cache. Fetching from WooCommerce directly...")
        try:
            response = wc_service.api.get(f"products/{product_id}")
            if response.status_code in (200, 201):
                product = response.json()
            else:
                logger.error(f"WooCommerce API returned {response.status_code} for product ID {product_id}")
        except Exception as e:
            logger.error(f"WooCommerce direct fetch exception for product ID {product_id}: {e}")

    if not product:
        return cart, f"Product with ID {product_id} not found in the store catalog."

    # Verify stock status
    stock_status = product.get("stock_status", "instock")
    if stock_status != "instock":
        return cart, f"Sorry, '{product.get('name')}' is currently out of stock."

    product_name = product.get("name", "Unknown Product")
    try:
        product_price = float(product.get("price", 0.0) or 0.0)
    except ValueError:
        product_price = 0.0

    images = product.get("images", [])
    img_src = ""
    if images:
        img_src = images[0] if isinstance(images[0], str) else images[0].get("src", "")

    # Check if product is already in the cart
    updated_cart = [dict(item) for item in cart]
    for item in updated_cart:
        if item.get("product_id") == product_id:
            new_qty = item["quantity"] + quantity
            if new_qty <= 0:
                return remove_from_cart_logic(cart, product_id)
            item["quantity"] = new_qty
            
            # Calculate subtotal
            subtotal = sum(cart_item["price"] * cart_item["quantity"] for cart_item in updated_cart)
            
            msg = f"✅ Updated **{product_name}** quantity in your cart.\n\n"
            msg += "### Current Cart\n"
            for cart_item in updated_cart:
                item_price = f"₹{cart_item['price']:.2f}"
                msg += f"• {cart_item['name']} × {cart_item['quantity']} — {item_price}\n"
            msg += f"\n**Subtotal: ₹{subtotal:.2f}**\n\n"
            msg += "[Proceed to Checkout](https://agilewellness.in/checkout/) | [View Cart](https://agilewellness.in/cart/)"
            
            logger.info(f"Updated '{product_name}' quantity to {item['quantity']}.")
            return updated_cart, msg

    if quantity <= 0:
        return cart, f"Cannot add negative or zero quantity ({quantity}) of '{product_name}' to your cart."

    # Add new item
    new_item = {
        "product_id": product_id,
        "name": product_name,
        "price": product_price,
        "quantity": quantity,
        "image": img_src
    }
    updated_cart.append(new_item)

    # Calculate subtotal
    subtotal = sum(item["price"] * item["quantity"] for item in updated_cart)
    
    msg = f"✅ **{product_name}** has been added to your cart.\n\n"
    msg += "### Current Cart\n"
    for item in updated_cart:
        item_price = f"₹{item['price']:.2f}"
        msg += f"• {item['name']} × {item['quantity']} — {item_price}\n"
    msg += f"\n**Subtotal: ₹{subtotal:.2f}**\n\n"
    msg += "[Proceed to Checkout](https://agilewellness.in/checkout/) | [View Cart](https://agilewellness.in/cart/)"
    
    logger.info(f"Added {quantity}x '{product_name}' (ID: {product_id}, Price: ₹{product_price:.2f}) to cart.")
    return updated_cart, msg


def remove_from_cart_logic(cart: List[Dict[str, Any]], product_id: int) -> Tuple[List[Dict[str, Any]], str]:
    """Stateless cart manipulation: Remove a product from the cart."""
    try:
        product_id = int(product_id)
    except (ValueError, TypeError):
        return cart, f"Invalid product ID: {product_id}."

    updated_cart = [dict(item) for item in cart]
    for idx, item in enumerate(updated_cart):
        if item.get("product_id") == product_id:
            removed_name = item.get("name", "Unknown Product")
            updated_cart.pop(idx)
            msg = f"Removed '{removed_name}' (ID: {product_id}) from your cart."
            logger.info(msg)
            return updated_cart, msg

    return cart, f"Product with ID {product_id} was not in your cart."


def calculate_total_logic(cart: List[Dict[str, Any]]) -> str:
    """Calculate subtotal and return a formatted cart summary."""
    if not cart:
        return "Your shopping cart is currently empty."

    result = "Current items in your cart:\n"
    subtotal = 0.0
    for item in cart:
        total_price = item.get("price", 0.0) * item.get("quantity", 1)
        subtotal += total_price
        result += f"- **{item.get('name')}** (ID: {item.get('product_id')}) | ₹{item.get('price'):.2f} x {item.get('quantity')} = ₹{total_price:.2f}\n"
    
    result += f"\n**Cart Total: ₹{subtotal:.2f}**"
    return result
