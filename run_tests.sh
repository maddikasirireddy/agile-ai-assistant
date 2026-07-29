#!/bin/bash
echo "=== TEST 1: Tell me about Charcoal & Lavender Soap ==="
curl -s -X POST -H "Content-Type: application/json" -d '{"message": "Tell me about Charcoal & Lavender Soap.", "customer_id": 55, "history": [], "cart": []}' http://127.0.0.1:8000/chat > t1_step1.json
REPLY=$(jq -r .reply t1_step1.json)
curl -s -X POST -H "Content-Type: application/json" -d "$(jq -n --arg msg "Charcoal & Lavender Soap - Handmade" --arg reply "$REPLY" '{message: $msg, customer_id: 55, history: [{role: "user", text: "Tell me about Charcoal & Lavender Soap."}, {role: "ai", text: $reply}], cart: []}')" http://127.0.0.1:8000/chat > t1_step2.json
jq -r .reply t1_step2.json

echo ""
echo "=== TEST 2: What is the price of Charcoal & Lavender Soap? ==="
curl -s -X POST -H "Content-Type: application/json" -d '{"message": "What is the price of Charcoal & Lavender Soap?", "customer_id": 56, "history": [], "cart": []}' http://127.0.0.1:8000/chat > t2_step1.json
REPLY=$(jq -r .reply t2_step1.json)
curl -s -X POST -H "Content-Type: application/json" -d "$(jq -n --arg msg "Charcoal & Lavender Soap - Handmade" --arg reply "$REPLY" '{message: $msg, customer_id: 56, history: [{role: "user", text: "What is the price of Charcoal & Lavender Soap?"}, {role: "ai", text: $reply}], cart: []}')" http://127.0.0.1:8000/chat > t2_step2.json
jq -r .reply t2_step2.json

echo ""
echo "=== TEST 3: Add Charcoal & Lavender Soap to my cart ==="
curl -s -X POST -H "Content-Type: application/json" -d '{"message": "Add Charcoal & Lavender Soap to my cart.", "customer_id": 57, "history": [], "cart": []}' http://127.0.0.1:8000/chat > t3_step1.json
REPLY=$(jq -r .reply t3_step1.json)
curl -s -X POST -H "Content-Type: application/json" -d "$(jq -n --arg msg "Charcoal & Lavender Soap - Handmade" --arg reply "$REPLY" '{message: $msg, customer_id: 57, history: [{role: "user", text: "Add Charcoal & Lavender Soap to my cart."}, {role: "ai", text: $reply}], cart: []}')" http://127.0.0.1:8000/chat > t3_step2.json
jq -r .reply t3_step2.json

