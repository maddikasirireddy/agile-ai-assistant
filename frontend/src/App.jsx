// App.jsx — Root Component for Agile Wellness AI Chatbot
// ─────────────────────────────────────────────────────────────
// Holds all application state:
//   - messages: list of chat messages
//   - input: current text in the textarea
//   - isLoading: true while waiting for AI response
//   - cart: list of shopping cart items
//   - isCartOpen: true if the cart drawer is visible
//   - customerId: simulated logged-in customer ID (defaults to 54)
//
// Orchestrates ChatWindow + InputBar + CartDrawer and calls backend API.
// ─────────────────────────────────────────────────────────────

import React, { useState, useCallback } from 'react'
import ChatWindow from './components/ChatWindow.jsx'
import InputBar from './components/InputBar.jsx'
import CartDrawer from './components/CartDrawer.jsx'
import { sendMessage } from './services/api.js'
import './App.css'

/**
 * Generate a unique ID for each message (used as React key)
 */
const generateId = () => `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`

/**
 * Get the current time formatted as HH:MM
 */
const getTime = () =>
  new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

const App = () => {
  // ── State ──────────────────────────────────────────────────
  const [messages, setMessages]   = useState([])          // chat history
  const [input, setInput]         = useState('')          // textarea value
  const [isLoading, setIsLoading] = useState(false)       // loading indicator
  const [cart, setCart]           = useState([])          // shopping cart items
  const [isCartOpen, setIsCartOpen] = useState(false)     // cart drawer toggle
  const [customerId, setCustomerId] = useState(54)        // logged-in customer simulator

  // ── Helper: append a message to the chat history ───────────
  const appendMessage = (role, text, isError = false) => {
    setMessages((prev) => [
      ...prev,
      { id: generateId(), role, text, time: getTime(), isError },
    ])
  }

  // ── Cart Handlers (for manual drawer changes) ──────────────
  const handleUpdateQuantity = (productId, newQty) => {
    if (newQty <= 0) {
      handleRemoveItem(productId)
      return
    }
    setCart((prev) =>
      prev.map((item) =>
        item.product_id === productId ? { ...item, quantity: newQty } : item
      )
    )
  }

  const handleRemoveItem = (productId) => {
    setCart((prev) => prev.filter((item) => item.product_id !== productId))
  }

  const handleClearCart = () => {
    setCart([])
  }

  // Add multiple items to cart (callback for the reorder button)
  const handleAddItemsToCart = useCallback((items) => {
    setCart((prev) => {
      const updated = [...prev]
      items.forEach((newItem) => {
        const existingIdx = updated.findIndex((i) => i.product_id === newItem.product_id)
        if (existingIdx !== -1) {
          updated[existingIdx].quantity += newItem.quantity
        } else {
          updated.push({
            product_id: newItem.product_id,
            name: newItem.name,
            price: newItem.price,
            quantity: newItem.quantity,
            image: newItem.image || ""
          })
        }
      })
      return updated
    })
    setIsCartOpen(true)
  }, [])

  // ── Send message handler ────────────────────────────────────
  const handleSend = useCallback(async () => {
    const trimmed = input.trim()
    if (!trimmed || isLoading) return

    // 1. Add the user's message to the chat
    appendMessage('user', trimmed)

    // 2. Clear the textarea immediately so it feels responsive
    setInput('')

    // 3. Show loading indicator
    setIsLoading(true)

    try {
      // 4. Map history payload to send to FastAPI
      const historyPayload = messages.map((m) => ({
        role: m.role,
        text: m.text,
      }))

      // 5. Call the FastAPI backend via our api.js service
      const response = await sendMessage(trimmed, historyPayload, cart, customerId)

      // 6. Add the AI's reply to the chat and update cart
      appendMessage('ai', response.reply)
      
      const newCart = response.cart || []
      
      // Auto-open cart drawer if items were added by the assistant
      const currentTotalQty = cart.reduce((sum, item) => sum + item.quantity, 0)
      const newTotalQty = newCart.reduce((sum, item) => sum + item.quantity, 0)
      if (newTotalQty > currentTotalQty) {
        setIsCartOpen(true)
      }
      
      setCart(newCart)
    } catch (err) {
      // 7. Show error as an AI bubble styled in red
      appendMessage('ai', err.message, true)
    } finally {
      // 8. Always hide the loading indicator when done
      setIsLoading(false)
    }
  }, [input, isLoading, messages, cart, customerId])

  // ── Suggestion chip handler ─────────────────────────────────
  const handleSuggest = useCallback(async (suggestion) => {
    const trimmed = suggestion.trim()
    if (!trimmed || isLoading) return
    appendMessage('user', trimmed)
    setIsLoading(true)
    try {
      const historyPayload = messages.map((m) => ({
        role: m.role,
        text: m.text,
      }))
      const response = await sendMessage(trimmed, historyPayload, cart, customerId)
      appendMessage('ai', response.reply)
      
      const newCart = response.cart || []
      
      const currentTotalQty = cart.reduce((sum, item) => sum + item.quantity, 0)
      const newTotalQty = newCart.reduce((sum, item) => sum + item.quantity, 0)
      if (newTotalQty > currentTotalQty) {
        setIsCartOpen(true)
      }
      
      setCart(newCart)
    } catch (err) {
      appendMessage('ai', err.message, true)
    } finally {
      setIsLoading(false)
    }
  }, [isLoading, messages, cart, customerId])

  // ── Clear conversation ──────────────────────────────────────
  const handleClear = () => {
    if (messages.length === 0) return
    setMessages([])
  }

  // ── Render ──────────────────────────────────────────────────
  return (
    <div className="app-shell">

      {/* ── Header ── */}
      <header className="app-header">
        <div className="header-brand">
          <div className="header-logo" aria-hidden="true">✦</div>
          <div className="header-title">
            <h1>Agile Wellness AI</h1>
            <span>E-commerce Assistant</span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center' }}>
          {/* Cart Drawer Toggle Button */}
          <button 
            className="cart-toggle-btn" 
            onClick={() => setIsCartOpen(true)}
            title="Open cart"
          >
            <span>🛒</span>
            <span>Cart</span>
            {cart.length > 0 && (
              <span className="cart-badge-number">
                {cart.reduce((a, b) => a + b.quantity, 0)}
              </span>
            )}
          </button>

          {/* Clear chat button */}
          {messages.length > 0 && (
            <button className="clear-btn" onClick={handleClear} title="Clear conversation">
              Clear chat
            </button>
          )}
          {/* Online status badge */}
          <div className="header-status">
            <div className="status-dot" aria-hidden="true" />
            <span>Online</span>
          </div>
        </div>
      </header>

      {/* ── Main chat area ── */}
      <main className="chat-body">
        {/* Scrollable message list */}
        <ChatWindow
          messages={messages}
          isLoading={isLoading}
          onSuggest={handleSuggest}
          onAddItemsToCart={handleAddItemsToCart}
        />

        {/* Input bar at the bottom */}
        <InputBar
          value={input}
          onChange={setInput}
          onSend={handleSend}
          disabled={isLoading}
        />
      </main>

      {/* Cart Slideout Drawer */}
      <CartDrawer
        isOpen={isCartOpen}
        onClose={() => setIsCartOpen(false)}
        cart={cart}
        onUpdateQuantity={handleUpdateQuantity}
        onRemove={handleRemoveItem}
        onClear={handleClearCart}
      />

    </div>
  )
}

export default App
