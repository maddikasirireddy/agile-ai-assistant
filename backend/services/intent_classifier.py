import os
import json
import logging
import google.generativeai as genai
from typing import Dict, Any

logger = logging.getLogger("agile_wellness")

def extract_entities(message: str) -> Dict[str, Any]:
    """
    Extracts structured intent and entities from a natural language message using Gemini.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
        
    model = genai.GenerativeModel("models/gemini-flash-latest")
    
    prompt = f"""
    You are a structured entity extractor for an e-commerce store selling organic wellness products (soaps, shampoos, etc).
    Analyze the user's message and extract the requested fields.
    
    Supported intents:
    - product_search (looking for a specific named product)
    - product_browsing (browsing multiple products, categories, or filtering)
    - product_detail (asking about ingredients, usage, price of a product)
    - recommendation (asking for advice for a concern)
    - add_to_cart (e.g., "Add it to my cart", "Add this", "Buy this", "Put it in my cart", "I want this")
    - remove_from_cart (e.g., "Remove it", "Remove this from my cart")
    - quantity_change (e.g., "Increase quantity", "Make it two")
    - view_cart
    - track_order
    - reorder
    - order_history
    - unknown (for greetings, FAQs, or off-topic)

    Return a JSON object matching this exact schema. If a value is missing, return null.
    Schema:
    {{
      "intent": "string",
      "product": "string | null",
      "category": "string | null",
      "ingredient": "string | null",
      "concern": "string | null",
      "quantity": "integer | null",
      "max_price": "number | null",
      "min_price": "number | null"
    }}

    Message to analyze: "{message}"
    """
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.0
            )
        )
        
        extracted = json.loads(response.text)
        
        # Log the debug info exactly as requested
        logger.info(
            f"\n[DEBUG ROUTING]\n"
            f"User Query: {message}\n"
            f"Detected Intent: {extracted.get('intent')}\n"
            f"Extracted Entities: {json.dumps(extracted, indent=2)}"
        )
        
        return extracted
        
    except Exception as e:
        logger.error(f"Failed to extract entities: {e}")
        return {
            "intent": "unknown",
            "product": None,
            "category": None,
            "ingredient": None,
            "concern": None,
            "quantity": None,
            "max_price": None,
            "min_price": None
        }
