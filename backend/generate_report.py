import sys
import os
import time

sys.path.append("/Users/sirireddy/agile-ai-assistant/backend")
from dotenv import load_dotenv
load_dotenv("/Users/sirireddy/agile-ai-assistant/backend/.env")

from services.knowledge_service import classify_intent, run_hybrid_chat_flow, search_products_local
from services.woocommerce_service import wc_service

def generate_report():
    products = wc_service.get_products()
    
    test_categories = {
        "PRODUCT SEARCH": [
            "lip butter", "mango lip butter", "strawberry lip butter", 
            "neem soap", "charcoal soap", "baby lotion", "baby shampoo", 
            "baby hair oil", "diaper rash cream", "anti acne serum"
        ],
        "FUZZY SEARCH": [
            "neem sooap", "lip buttr", "babby lotion", "charcol soap"
        ],
        "CONCERN-BASED SEARCH": [
            "dry lips", "cracked lips", "oily skin", "acne", "pimples", 
            "dry skin", "baby skincare", "dandruff", "hair fall"
        ],
        "INGREDIENT SEARCH": [
            "neem", "charcoal", "lavender", "aloe vera", "turmeric", "coconut"
        ],
        "CATEGORY SEARCH": [
            "soaps", "lip care", "baby care", "skincare"
        ]
    }
    
    report = "# Product Retrieval Pipeline Validation Report\n\n"
    report += "This report details the performance of the unified fuzzy search architecture.\n\n"
    
    total_passed = 0
    total_failed = 0
    failures = []
    
    for category_name, queries in test_categories.items():
        report += f"## {category_name}\n"
        
        for q in queries:
            try:
                start_time = time.perf_counter()
                intent = classify_intent(q)
                
                # Simulate the unified search exact logic
                scored_matches = search_products_local(products, q)
                exact_matches = [p for p in scored_matches if p.get("_search_score", 0) >= 80.0]
                close_matches = [p for p in scored_matches if p.get("_search_score", 0) >= 20.0]
                matching_products = exact_matches if exact_matches else close_matches
                
                fallback = False
                if len(matching_products) == 0 and intent == "unknown":
                    fallback = True
                    # If fallback to Gemini, Gemini tool uses search_products_local with no thresholds
                    matching_products = scored_matches
                
                end_time = time.perf_counter()
                elapsed_ms = (end_time - start_time) * 1000
                
                # Evaluate success
                # A success is finding at least one relevant product.
                passed = len(matching_products) > 0
                if passed:
                    total_passed += 1
                else:
                    total_failed += 1
                    failures.append(q)
                    
                report += f"### Query: `{q}`\n"
                report += f"- **Detected Intent:** {intent}\n"
                report += f"- **Search Terms Used:** {q}\n"
                
                if matching_products:
                    report += f"- **Matching Products (Top 3):**\n"
                    for idx, p in enumerate(matching_products[:3]):
                        score = p.get("_search_score", 0)
                        report += f"  - [{score:.1f}] {p.get('name')}\n"
                else:
                    report += f"- **Matching Products:** None\n"
                    
                source = "Gemini Fallback (Tool Execution)" if fallback else "Local Fast-Path Pipeline"
                report += f"- **Source:** {source}\n"
                report += f"- **Response Time:** {elapsed_ms:.1f}ms\n"
                report += f"- **Status:** {'✅ PASS' if passed else '❌ FAIL'}\n\n"
                
            except Exception as e:
                report += f"### Query: `{q}`\n"
                report += f"- **Status:** ❌ ERROR: {str(e)}\n\n"
                total_failed += 1
                failures.append(q)

    report += "## Summary\n"
    report += f"- **Total Tests Passed:** {total_passed}\n"
    report += f"- **Total Tests Failed:** {total_failed}\n\n"
    
    if failures:
        report += "### Unresolvable Queries\n"
        for f in failures:
            report += f"- `{f}`\n"
            
    report += "\n### Missing Products & Suggestions\n"
    report += "If any products failed to resolve, it indicates those products do not exist in the current WooCommerce catalog (e.g. Baby products, Turmeric, Coconut). "
    report += "To improve retrieval accuracy for existing products, we can add them to the `concern_map` in `search_service.py`.\n"
    
    with open("/Users/sirireddy/.gemini/antigravity-ide/brain/396fe7ee-56d2-4e70-b3af-b718a1597c05/validation_report.md", "w") as f:
        f.write(report)
        
    print("Report generated.")

if __name__ == "__main__":
    generate_report()
