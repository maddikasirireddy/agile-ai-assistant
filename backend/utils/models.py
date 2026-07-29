from pydantic import BaseModel
from typing import List, Optional

class MessageHistoryItem(BaseModel):
    """Represents an item in the chat message history."""
    role: str  # 'user' or 'ai'
    text: str

class CartItem(BaseModel):
    """Represents a product item in the shopping cart."""
    product_id: int
    name: str
    price: float
    quantity: int
    image: str

class ChatRequest(BaseModel):
    """Request payload schema for the /chat endpoint."""
    message: str
    customer_id: Optional[int] = None
    history: List[MessageHistoryItem] = []
    cart: List[CartItem] = []


class ChatResponse(BaseModel):
    """Response payload schema for the /chat endpoint."""
    reply: str
    cart: List[CartItem]
