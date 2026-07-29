import sys
import unittest
from unittest.mock import patch, MagicMock

# Add backend directory to path
sys.path.append("/Users/sirireddy/agile-ai-assistant/backend")

from dotenv import load_dotenv
load_dotenv("/Users/sirireddy/agile-ai-assistant/backend/.env")

from services.knowledge_service import run_hybrid_chat_flow
from services.session_service import get_session_state, reset_session

class TestHybridFeatures(unittest.TestCase):

    @patch("services.woocommerce_service.wc_service.get_products")
    def test_production_scenarios(self, mock_get_products):
        # Setup catalog
        mock_get_products.return_value = [
            {
                "id": 9325,
                "name": "Neem Soap - Handmade",
                "price": "200.00",
                "permalink": "https://agilewellness.in/neem-soap",
                "description": "Nourishing handmade neem soap.",
                "short_description": "Neem soap",
                "ingredients": ["neem", "basil"],
                "stock_status": "instock",
                "skin_types": ["oily"],
                "hair_types": [],
                "concerns": ["acne"],
                "recommended_for": ["oily skin", "acne"],
                "avoid_for": [],
                "product_type": "soap",
                "body_area": "face",
                "baby_safe": False
            },
            {
                "id": 9452,
                "name": "Anti-Acne Serum",
                "price": "350.00",
                "permalink": "https://agilewellness.in/anti-acne-serum",
                "description": "Reduces blemishes and controls excess oil.",
                "short_description": "Cleanse and heal",
                "ingredients": ["tea tree", "salicylic acid"],
                "stock_status": "instock",
                "skin_types": ["oily", "combination"],
                "hair_types": [],
                "concerns": ["acne", "pimples"],
                "recommended_for": ["oily skin", "acne"],
                "avoid_for": ["very dry skin"],
                "product_type": "serum",
                "body_area": "face",
                "baby_safe": False
            },
            {
                "id": 9431,
                "name": "Charcoal & Lavender Soap - Handmade",
                "price": "220.00",
                "permalink": "https://agilewellness.in/charcoal-lavender",
                "description": "Clarifying charcoal soap.",
                "short_description": "Lavender soap",
                "ingredients": ["charcoal", "lavender"],
                "stock_status": "instock",
                "skin_types": ["oily"],
                "hair_types": [],
                "concerns": ["clogged pores"],
                "recommended_for": ["clogged pores"],
                "avoid_for": [],
                "product_type": "soap",
                "body_area": "face",
                "baby_safe": False
            },
            {
                "id": 9412,
                "name": "Lavender Soap - Handmade",
                "price": "180.00",
                "permalink": "https://agilewellness.in/lavender-soap",
                "description": "Relaxing lavender.",
                "short_description": "Relaxing bath",
                "ingredients": ["lavender oil"],
                "stock_status": "instock",
                "skin_types": ["normal"],
                "hair_types": [],
                "concerns": [],
                "recommended_for": [],
                "avoid_for": [],
                "product_type": "soap",
                "body_area": "body",
                "baby_safe": False
            }
        ]

        sid = "test_scenarios_session"
        reset_session(sid)
        cart = []

        # ====================================================
        # Test 1
        # ====================================================
        
        # User: Tell me about Neem Soap.
        reply, cart = run_hybrid_chat_flow("Tell me about Neem Soap.", [], cart, session_id=sid)
        self.assertIn("Neem Soap - Handmade", reply)
        
        # User: Price?
        history = [
            {"role": "user", "text": "Tell me about Neem Soap."},
            {"role": "ai", "text": reply}
        ]
        reply_price, cart = run_hybrid_chat_flow("Price?", history, cart, session_id=sid)
        self.assertIn("price of **neem soap - handmade** is ₹200", reply_price.lower())

        # ====================================================
        # Test 1b: Typo and Direct Actions
        # ====================================================
        reset_session(sid)
        cart = []
        
        # User: Tell me about Neem sooap (testing typo)
        reply_typo, cart = run_hybrid_chat_flow("Tell me about Neem sooap", [], cart, session_id=sid)
        self.assertIn("Neem Soap - Handmade", reply_typo)
        
        # User: What's the price of Neem Soap?
        reset_session(sid)
        reply_price2, cart = run_hybrid_chat_flow("What's the price of Neem Soap?", [], cart, session_id=sid)
        self.assertIn("price of **neem soap - handmade** is ₹200", reply_price2.lower())
        
        # User: Add Neem Soap to my cart
        reset_session(sid)
        reply_add, cart = run_hybrid_chat_flow("Add Neem Soap to my cart", [], cart, session_id=sid)
        self.assertIn("added", reply_add.lower())
        self.assertEqual(len(cart), 1)
        self.assertEqual(cart[0]["product_id"], 9325)

        # ====================================================
        # Test 2
        # ====================================================
        reset_session(sid)
        cart = []
        
        # User: Recommend a product for acne.
        reply, cart = run_hybrid_chat_flow("Recommend a product for acne.", [], cart, session_id=sid)
        self.assertIn("Anti-Acne Serum", reply) # (Highest ranked matching concern product)
        
        # User: Tell me about that product.
        history = [
            {"role": "user", "text": "Recommend a product for acne."},
            {"role": "ai", "text": reply}
        ]
        reply, cart = run_hybrid_chat_flow("Tell me about that product.", history, cart, session_id=sid)
        self.assertIn("Anti-Acne Serum", reply)
        self.assertIn("reduces blemishes", reply.lower())
        
        # User: What's the price?
        history.extend([
            {"role": "user", "text": "Tell me about that product."},
            {"role": "ai", "text": reply}
        ])
        reply, cart = run_hybrid_chat_flow("What's the price?", history, cart, session_id=sid)
        self.assertIn("price of **anti-acne serum** is ₹350", reply.lower())
        
        # User: Add it to my cart.
        history.extend([
            {"role": "user", "text": "What's the price?"},
            {"role": "ai", "text": reply}
        ])
        reply, cart = run_hybrid_chat_flow("Add it to my cart.", history, cart, session_id=sid)
        self.assertIn("added", reply.lower())
        self.assertEqual(len(cart), 1)
        self.assertEqual(cart[0]["product_id"], 9452)

        # ====================================================
        # Test 3
        # ====================================================
        reset_session(sid)
        cart = []
        
        # User: Tell me about Charcoal & Lavender Soap.
        reply1, cart = run_hybrid_chat_flow("Tell me about Charcoal & Lavender Soap.", [], cart, session_id=sid)
        self.assertIn("Did you mean one of these products?", reply1)
        self.assertIn("Charcoal & Lavender Soap", reply1)
        self.assertIn("Lavender Soap", reply1)
        
        # User: Charcoal & Lavender Soap - Handmade
        history = [
            {"role": "user", "text": "Tell me about Charcoal & Lavender Soap."},
            {"role": "ai", "text": reply1}
        ]
        reply2, cart = run_hybrid_chat_flow("Charcoal & Lavender Soap - Handmade", history, cart, session_id=sid)
        self.assertIn("Charcoal & Lavender Soap - Handmade", reply2)
        self.assertIn("clarifying charcoal", reply2.lower()) # returns product description
        self.assertNotIn("Did you mean", reply2) # does not ask again

        # ====================================================
        # Test 4
        # ====================================================
        history.extend([
            {"role": "user", "text": "Charcoal & Lavender Soap - Handmade"},
            {"role": "ai", "text": reply2}
        ])
        reply3, cart = run_hybrid_chat_flow("Price?", history, cart, session_id=sid)
        self.assertIn("price of **charcoal & lavender soap - handmade** is ₹220", reply3.lower())

        # ====================================================
        # Test 5
        # ====================================================
        history.extend([
            {"role": "user", "text": "Price?"},
            {"role": "ai", "text": reply3}
        ])
        reply4, cart = run_hybrid_chat_flow("Ingredients?", history, cart, session_id=sid)
        self.assertIn("contains the following ingredients", reply4.lower())
        self.assertIn("Charcoal", reply4)

if __name__ == "__main__":
    unittest.main()
