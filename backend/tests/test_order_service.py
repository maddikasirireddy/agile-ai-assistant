import sys
import unittest
from unittest.mock import MagicMock, patch

# Add backend directory to path
sys.path.append("/Users/sirireddy/agile-ai-assistant/backend")

from dotenv import load_dotenv
load_dotenv("/Users/sirireddy/agile-ai-assistant/backend/.env")

from services.order_service import (
    get_customer_orders, 
    track_latest_order, 
    list_orders, 
    order_details, 
    reorder_last_order
)

class TestOrderService(unittest.TestCase):
    def setUp(self):
        # Mock order return value
        self.mock_orders = [
            {
                "id": 9766,
                "status": "processing",
                "date_created": "2026-07-15T12:00:00",
                "total": "850.00",
                "currency_symbol": "₹",
                "payment_method_title": "UPI",
                "date_paid": "2026-07-15T12:05:00",
                "shipping_lines": [{"method_title": "Standard Delivery"}],
                "meta_data": [
                    {"key": "_tracking_number", "value": "AW23948723"},
                    {"key": "_estimated_delivery", "value": "2026-07-18"}
                ],
                "line_items": [
                    {"product_id": 9325, "name": "Neem Soap", "quantity": 2, "price": 200.00},
                    {"product_id": 9493, "name": "Neem Powder", "quantity": 1, "price": 450.00}
                ]
            },
            {
                "id": 9720,
                "status": "completed",
                "date_created": "2026-07-01T10:00:00",
                "total": "420.00",
                "currency_symbol": "₹",
                "payment_method_title": "Cash on delivery",
                "date_paid": "2026-07-01T10:00:00",
                "shipping_lines": [{"method_title": "Standard Delivery"}],
                "meta_data": [],
                "line_items": [
                    {"product_id": 9325, "name": "Neem Soap", "quantity": 2, "price": 210.00}
                ]
            }
        ]

    @patch("services.woocommerce_service.wc_service.api.get")
    @patch("services.woocommerce_service.wc_service.get_products")
    def test_get_customer_orders(self, mock_get_products, mock_api_get):
        # Set up mocks
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_orders
        mock_api_get.return_value = mock_response
        
        # Mock product cache lookup
        mock_get_products.return_value = [
            {"id": 9325, "name": "Neem Soap", "price": "200", "images": [{"src": "neem_soap.jpg"}]},
            {"id": 9493, "name": "Neem Powder", "price": "450", "images": [{"src": "neem_powder.jpg"}]}
        ]

        orders = get_customer_orders(54)
        
        self.assertEqual(len(orders), 2)
        self.assertEqual(orders[0]["id"], 9766)
        self.assertEqual(orders[0]["status"], "processing")
        self.assertEqual(orders[0]["payment_status"], "paid")
        self.assertEqual(orders[0]["tracking_number"], "AW23948723")
        self.assertEqual(orders[0]["estimated_delivery"], "2026-07-18")
        self.assertEqual(orders[0]["line_items"][0]["image"], "neem_soap.jpg")
        
        mock_api_get.assert_called_with("orders", params={"customer": 54, "per_page": 100})

    @patch("services.order_service.get_customer_orders")
    def test_track_latest_order(self, mock_get_customer_orders):
        # Setup parsed orders mock
        mock_get_customer_orders.return_value = [
            {
                "id": 9766,
                "status": "processing",
                "payment_status": "paid",
                "date": "2026-07-15",
                "total": "850.00",
                "currency": "₹",
                "shipping_method": "Standard Delivery",
                "tracking_number": "AW23948723",
                "estimated_delivery": "2026-07-18",
                "line_items": [
                    {"product_id": 9325, "name": "Neem Soap", "quantity": 2, "price": 200.0},
                    {"product_id": 9493, "name": "Neem Powder", "quantity": 1, "price": 450.0}
                ]
            }
        ]

        tracking_res = track_latest_order(54)
        
        self.assertIn("📦 Order #9766", tracking_res)
        self.assertIn("Status\n🟡 Processing", tracking_res)
        self.assertIn("Payment\n🟢 Paid", tracking_res)
        self.assertIn("15 July 2026", tracking_res)
        self.assertIn("• Neem Soap ×2", tracking_res)
        self.assertIn("Total\n₹850", tracking_res)
        self.assertIn("Tracking Number\nAW23948723", tracking_res)
        self.assertIn("Estimated Delivery\n18 July 2026", tracking_res)

    @patch("services.order_service.get_customer_orders")
    def test_list_orders(self, mock_get_customer_orders):
        mock_get_customer_orders.return_value = [
            {
                "id": 9766,
                "status": "processing",
                "payment_status": "paid",
                "date": "2026-07-15",
                "total": "850.00",
                "currency": "₹"
            },
            {
                "id": 9720,
                "status": "completed",
                "payment_status": "paid",
                "date": "2026-07-01",
                "total": "420.00",
                "currency": "₹"
            }
        ]

        result = list_orders(54)
        self.assertEqual(result["type"], "order_history")
        self.assertEqual(len(result["orders"]), 2)
        self.assertEqual(result["orders"][0]["id"], 9766)
        self.assertEqual(result["orders"][1]["id"], 9720)

    @patch("services.order_service.get_customer_orders")
    def test_order_details(self, mock_get_customer_orders):
        mock_get_customer_orders.return_value = [
            {
                "id": 9766,
                "status": "processing",
                "payment_status": "paid",
                "date": "2026-07-15",
                "total": "850.00",
                "currency": "₹",
                "shipping_method": "Standard Delivery",
                "line_items": []
            }
        ]

        # Valid order ID
        details_ok = order_details(54, 9766)
        self.assertIn("📦 Order #9766", details_ok)

        # Invalid/Other customer order ID
        details_fail = order_details(54, 9999)
        self.assertIn("not found, or it does not belong", details_fail)

    @patch("services.order_service.get_customer_orders")
    def test_reorder_last_order(self, mock_get_customer_orders):
        mock_get_customer_orders.return_value = [
            {
                "id": 9766,
                "line_items": [
                    {"product_id": 9325, "name": "Neem Soap", "quantity": 2, "price": 200.0, "image": "neem_soap.jpg"}
                ]
            }
        ]

        result = reorder_last_order(54)
        self.assertEqual(result["type"], "reorder")
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["product_id"], 9325)
        self.assertEqual(result["items"][0]["quantity"], 2)
        self.assertEqual(result["items"][0]["name"], "Neem Soap")

if __name__ == "__main__":
    unittest.main()
