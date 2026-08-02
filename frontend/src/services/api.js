// services/api.js
// ─────────────────────────────────────────────────────────────
// Handles all HTTP communication with the FastAPI backend.
// Using Axios for cleaner request/response handling.
// ─────────────────────────────────────────────────────────────

import axios from 'axios'

// Base URL of our FastAPI backend (configured via environment variables)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://agile-ai-assistant.onrender.com'

// Create a reusable Axios instance with default settings
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * sendMessage — sends the user's message, history, cart, and customerId to the /chat endpoint
 * @param {string} message — the user's text input
 * @param {Array} history — previous messages [{"role": "user"|"ai", "text": string}]
 * @param {Array} cart — current cart items
 * @param {number|null} customerId — the logged in WooCommerce customer ID
 * @returns {Promise<{reply: string, cart: Array}>} — the AI's reply and updated cart
 */
export const sendMessage = async (message, history = [], cart = [], customerId = null) => {
  try {
    // POST to /chat with the user message, history, cart, and customer_id in the request body
    const response = await apiClient.post('/chat', { 
      message, 
      history, 
      cart, 
      customer_id: customerId 
    })
    // The backend returns: { reply: "...", cart: [...], cart_actions: [...] }
    return response.data
  } catch (error) {
    // Provide a friendly error message instead of crashing
    console.error('API error:', error)
    throw new Error(
      error.response?.data?.detail || 'Failed to connect to the server. Please try again.'
    )
  }
}

