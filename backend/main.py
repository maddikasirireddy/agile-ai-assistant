# backend/main.py

import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from utils.logging_config import logger
from utils.models import ChatRequest, ChatResponse
from services.knowledge_service import run_hybrid_chat_flow

# Initialize FastAPI App
app = FastAPI(
    title="Agile Wellness AI Backend",
    description="Production-ready hybrid FastAPI backend for Agile Wellness AI shopping assistant.",
    version="2.0"
)

# CORS Configuration
# Allow local React dev server (http://localhost:5173) and production configurations
allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]
env_cors = os.getenv("ALLOWED_ORIGINS")
if env_cors:
    allowed_origins.extend([origin.strip() for origin in env_cors.split(",")])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------
# Global Security & Error Handlers
# ----------------------------------------------------

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Log and return HTTP exceptions securely."""
    logger.warning(f"HTTP Error: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to block raw stack traces and prevent leaking API credentials."""
    logger.exception(f"Unhandled system error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Our team has been notified. Please try again."}
    )

# ----------------------------------------------------
# Routes
# ----------------------------------------------------

@app.get("/")
def root():
    """Service status checking endpoint."""
    return {
        "status": "ok",
        "service": "Agile Wellness AI Hybrid Backend",
        "version": "2.0"
    }

import uuid

@app.post("/chat")
async def chat(chat_request: ChatRequest, fastapi_request: Request):
    """
    Main chat handler endpoint.
    Routes incoming chats to the hybrid local-first pipeline to minimize API calls.
    Manages session cookies for conversation tracking.
    """
    user_message = chat_request.message.strip()

    if not user_message:
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty."
        )

    # Sanitize user input by removing script tags
    sanitized_message = user_message.replace("<script>", "").replace("</script>", "")

    # 1. Resolve Session ID
    session_id = fastapi_request.cookies.get("session_id")
    if not session_id:
        if chat_request.customer_id is not None:
            session_id = f"customer_{chat_request.customer_id}"
        else:
            # Fallback fingerprinting for guest local development (CORS)
            client_ip = fastapi_request.client.host if fastapi_request.client else "unknown"
            first_user_msg = next((m.text for m in chat_request.history if m.role == "user"), sanitized_message)
            fingerprint = f"{client_ip}_{first_user_msg}"
            from services.session_service import FINGERPRINTS
            if fingerprint in FINGERPRINTS:
                session_id = FINGERPRINTS[fingerprint]
            else:
                session_id = str(uuid.uuid4())
                FINGERPRINTS[fingerprint] = session_id

    # Execute chat session using our hybrid local-first orchestrator
    reply, updated_cart = run_hybrid_chat_flow(
        message=sanitized_message,
        history=[msg.dict() for msg in chat_request.history],
        cart=[item.dict() for item in chat_request.cart],
        customer_id=chat_request.customer_id,
        session_id=session_id
    )

    # Diff the cart to generate cart_actions for the frontend WooCommerce sync
    old_cart_dict = {item.product_id: item.quantity for item in chat_request.cart}
    new_cart_dict = {item.get("product_id"): item.get("quantity") for item in updated_cart}
    
    cart_actions = []
    for pid, qty in new_cart_dict.items():
        if pid is not None and old_cart_dict.get(pid) != qty:
            cart_actions.append({"action": "set_quantity", "product_id": pid, "quantity": qty})
            
    for pid in old_cart_dict:
        if pid not in new_cart_dict:
            cart_actions.append({"action": "set_quantity", "product_id": pid, "quantity": 0})

    # Return response and set session cookie
    response = ChatResponse(
        reply=reply,
        cart=updated_cart,
        cart_actions=cart_actions
    )
    response_obj = JSONResponse(content=response.dict())
    response_obj.set_cookie(
        "session_id", 
        session_id, 
        max_age=1800,  # 30 mins
        httponly=True, 
        samesite="lax"
    )
    return response_obj