import time
import logging
from typing import List, Dict, Any, Optional
from services.woocommerce_service import wc_service

logger = logging.getLogger("agile_wellness")

def get_customer_orders(customer_id: int) -> List[Dict[str, Any]]:
    """
    Retrieve all WooCommerce orders for the given customer ID.
    Returns a list of parsed order dictionaries.
    """
    logger.info(f"Retrieving WooCommerce orders for customer ID {customer_id}...")
    start_time = time.perf_counter()
    try:
        # Request orders matching this customer ID
        response = wc_service.api.get("orders", params={"customer": customer_id, "per_page": 100})
        elapsed = time.perf_counter() - start_time
        logger.info(f"WooCommerce API GET /orders?customer={customer_id} took {elapsed:.2f}s")
        
        if response.status_code not in (200, 201):
            logger.error(f"WooCommerce returned status {response.status_code} for customer {customer_id}")
            return []
            
        orders = response.json()
        parsed_orders = []
        
        # Load products cache to resolve prices/images where possible
        products = wc_service.get_products()
        product_map = {p["id"]: p for p in products}

        for order in orders:
            order_id = order.get("id")
            status = order.get("status", "unknown")
            date_created = order.get("date_created", "").split("T")[0]
            total = order.get("total")
            currency = order.get("currency_symbol", "₹")
            payment_method = order.get("payment_method_title", "N/A")
            
            # Payment status inference
            date_paid = order.get("date_paid")
            if date_paid or status in ("completed", "processing"):
                payment_status = "Paid"
            elif status in ("pending", "failed"):
                payment_status = "Unpaid"
            elif status == "cancelled":
                payment_status = "Cancelled"
            else:
                payment_status = "Awaiting Payment"
                
            # Shipping method
            shipping_method = "Standard Delivery"
            if order.get("shipping_lines"):
                shipping_method = order["shipping_lines"][0].get("method_title", "Standard Delivery")

            # Parse metadata (tracking & estimated delivery)
            tracking_number = None
            estimated_delivery = None
            for meta in order.get("meta_data", []):
                key = str(meta.get("key", "")).lower()
                val = meta.get("value", "")
                if val:
                    if any(t in key for t in ["tracking", "shipment", "carrier", "shipping_provider", "hawb"]):
                        tracking_number = str(val)
                    if any(t in key for t in ["delivery", "estimated", "expected"]):
                        estimated_delivery = str(val)

            # Parse line items
            line_items = []
            for item in order.get("line_items", []):
                pid = item.get("product_id")
                p_name = item.get("name", "Unknown Product")
                qty = item.get("quantity", 1)
                
                # Fetch image & price from product map if available
                img_src = ""
                price = 0.0
                try:
                    price = float(item.get("price", 0.0) or 0.0)
                except ValueError:
                    pass
                    
                if pid in product_map:
                    img_src = product_map[pid].get("images", [{}])[0].get("src", "")
                    try:
                        price = float(product_map[pid].get("price", price))
                    except ValueError:
                        pass
                
                line_items.append({
                    "product_id": pid,
                    "name": p_name,
                    "quantity": qty,
                    "price": price,
                    "image": img_src
                })

            parsed_orders.append({
                "id": order_id,
                "status": status,
                "payment_status": payment_status.lower(),
                "total": total,
                "currency": currency,
                "date": date_created,
                "shipping_method": shipping_method,
                "tracking_number": tracking_number,
                "estimated_delivery": estimated_delivery,
                "line_items": line_items,
                "payment_method": payment_method
            })
            
        return parsed_orders
    except Exception as e:
        logger.exception(f"Exception retrieving customer orders for ID {customer_id}: {e}")
        return []

def track_latest_order(customer_id: int) -> str:
    """
    Retrieve the newest order for the customer and format it as a beautiful tracking response.
    """
    orders = get_customer_orders(customer_id)
    if not orders:
        return "You do not have any orders in our system yet."

    # First order is the newest since WooCommerce returns orders in reverse chronological order
    latest = orders[0]
    return format_order_tracking_markdown(latest)

def list_orders(customer_id: int) -> Dict[str, Any]:
    """
    Return all customer orders in a structured JSON suitable for frontend rendering.
    """
    orders = get_customer_orders(customer_id)
    # Map to expected frontend schema
    formatted_orders = []
    for o in orders:
        formatted_orders.append({
            "id": o["id"],
            "status": o["status"],
            "payment_status": o["payment_status"],
            "date": o["date"],
            "total": o["total"],
            "currency": o["currency"] or "INR"
        })
    return {
        "type": "order_history",
        "orders": formatted_orders
    }

def order_details(customer_id: int, order_number: int) -> str:
    """
    Return detailed information for a requested order, verifying it belongs to the authenticated customer.
    """
    orders = get_customer_orders(customer_id)
    matched_order = None
    for o in orders:
        if o["id"] == order_number:
            matched_order = o
            break
            
    if not matched_order:
        return f"Order #{order_number} not found, or it does not belong to your account."

    return format_order_tracking_markdown(matched_order)

def reorder_last_order(customer_id: int) -> Dict[str, Any]:
    """
    Extract products and quantities from the newest order to allow reordering.
    """
    orders = get_customer_orders(customer_id)
    if not orders:
        return {
            "type": "reorder",
            "items": [],
            "error": "You do not have any previous orders to reorder."
        }

    latest = orders[0]
    reorder_items = []
    for item in latest.get("line_items", []):
        reorder_items.append({
            "product_id": item["product_id"],
            "name": item["name"],
            "price": item["price"],
            "quantity": item["quantity"],
            "image": item["image"]
        })

    return {
        "type": "reorder",
        "items": reorder_items
    }

def format_order_tracking_markdown(order: Dict[str, Any]) -> str:
    """
    Format a parsed order dictionary into a professional tracking Markdown response.
    """
    items_lines = []
    for item in order.get("line_items", []):
        items_lines.append(f"• {item['name']} ×{item['quantity']}")
    items_str = "\n".join(items_lines)

    status_icon = "🟢" if order["status"] == "completed" else "🟡" if order["status"] in ("processing", "on-hold") else "🔴"
    payment_icon = "🟢" if order["payment_status"] == "paid" else "🟡" if order["payment_status"] == "awaiting payment" else "🔴"

    result = f"📦 Order #{order['id']}\n\n"
    result += f"Status\n{status_icon} {order['status'].capitalize()}\n\n"
    result += f"Payment\n{payment_icon} {order['payment_status'].capitalize()}\n\n"
    
    # Format placed date cleanly: e.g. "2026-07-15" to "15 July 2026"
    date_str = order['date']
    try:
        from datetime import datetime
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        formatted_date = dt.strftime("%d %B %Y")
    except Exception:
        formatted_date = date_str
        
    result += f"Placed\n{formatted_date}\n\n"
    result += f"Items\n{items_str}\n\n"
    # Clean decimal values from total if they are whole numbers (.00)
    try:
        total_val = float(order['total'])
        total_str = f"{int(total_val)}" if total_val.is_integer() else f"{total_val:.2f}"
    except (ValueError, TypeError):
        total_str = order['total']

    result += f"Total\n{order['currency']}{total_str}\n\n"
    result += f"Shipping\n{order['shipping_method']}\n\n"
    
    if order.get("tracking_number"):
        result += f"Tracking Number\n{order['tracking_number']}\n\n"
        
    if order.get("estimated_delivery"):
        # Format estimated date cleanly if it is in YYYY-MM-DD
        est_str = order['estimated_delivery']
        try:
            from datetime import datetime
            dt = datetime.strptime(est_str, "%Y-%m-%d")
            formatted_est = dt.strftime("%d %B %Y")
        except Exception:
            formatted_est = est_str
        result += f"Estimated Delivery\n{formatted_est}\n"
        
    return result.strip()

def track_order_logic(order_id: int) -> str:
    """
    Fallback for non-customer order tracking (backward compatibility).
    """
    try:
        order_id = int(order_id)
        response = wc_service.api.get(f"orders/{order_id}")
        if response.status_code not in (200, 201):
            return f"Order with ID #{order_id} could not be found."
            
        order = response.json()
        
        # Shipping lines
        shipping_method = "Standard Delivery"
        if order.get("shipping_lines"):
            shipping_method = order["shipping_lines"][0].get("method_title", "Standard Delivery")
            
        # Parse tracking
        tracking_number = None
        for meta in order.get("meta_data", []):
            key = str(meta.get("key", "")).lower()
            val = meta.get("value", "")
            if val and any(t in key for t in ["tracking", "shipment", "carrier"]):
                tracking_number = str(val)
                break
                
        items_list = [f"• {i['name']} ×{i['quantity']}" for i in order.get("line_items", [])]
        items_str = "\n".join(items_list)
        
        # Clean decimal values from total if they are whole numbers (.00)
        try:
            total_val = float(order.get('total', 0))
            total_str = f"{int(total_val)}" if total_val.is_integer() else f"{total_val:.2f}"
        except (ValueError, TypeError):
            total_str = order.get('total', '0')

        result = f"📦 Order #{order_id}\n\n"
        result += f"Status\n{order.get('status', 'unknown').capitalize()}\n\n"
        result += f"Placed\n{order.get('date_created', '').split('T')[0]}\n\n"
        result += f"Items\n{items_str}\n\n"
        result += f"Total\n{order.get('currency_symbol', '₹')}{total_str}\n\n"
        result += f"Shipping\n{shipping_method}\n"
        if tracking_number:
            result += f"\nTracking Number\n{tracking_number}\n"
        return result
    except Exception as e:
        return f"Unable to retrieve tracking details: {str(e)}"
