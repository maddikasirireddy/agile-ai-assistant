from pydantic import BaseModel
from typing import List, Optional

class CartItem(BaseModel):
    product_id: int
    name: str
    price: float
    quantity: int
    image: str

old_cart = [CartItem(product_id=123, name="A", price=10, quantity=1, image="")]
new_cart = [{"product_id": 123, "name": "A", "price": 10, "quantity": 2, "image": ""}]

old_cart_dict = {item.product_id: item.quantity for item in old_cart}
new_cart_dict = {item.get("product_id"): item.get("quantity") for item in new_cart}

cart_actions = []
for pid, qty in new_cart_dict.items():
    if pid is not None and old_cart_dict.get(pid) != qty:
        cart_actions.append({"action": "set_quantity", "product_id": pid, "quantity": qty})
        
for pid in old_cart_dict:
    if pid not in new_cart_dict:
        cart_actions.append({"action": "set_quantity", "product_id": pid, "quantity": 0})

print(cart_actions)
