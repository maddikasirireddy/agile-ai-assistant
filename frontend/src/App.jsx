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

import React, { useState, useCallback, useEffect } from 'react'
import ChatWindow from './components/ChatWindow.jsx'
import InputBar from './components/InputBar.jsx'
import CartDrawer from './components/CartDrawer.jsx'
import { sendMessage } from './services/api.js'
import * as wcCartService from './services/wcCart.js'
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
  const [messages, setMessages] = useState([])          // chat history
  const [input, setInput] = useState('')          // textarea value
  const [isLoading, setIsLoading] = useState(false)       // loading indicator
  const [cart, setCart] = useState([])          // shopping cart items
  const [isCartOpen, setIsCartOpen] = useState(false)     // cart drawer toggle
  const [customerId, setCustomerId] = useState(54)        // logged-in customer simulator
  const [isChatOpen, setIsChatOpen] = useState(false)
  const [hasOpened, setHasOpened] = useState(false)

  // ── Initialization ───────────────────────────────────────────
  useEffect(() => {
    wcCartService.fetchCart()
      .then(setCart)
      .catch(err => console.error("Failed to fetch initial WooCommerce cart:", err));
  }, []);

  // ── Keyboard Navigation ────────────────────────────────────
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isChatOpen) {
        setIsChatOpen(false)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isChatOpen])

  // ── Notify Parent Window ───────────────────────────────────
  useEffect(() => {
    // Send message to parent WordPress site to resize the iframe dynamically
    window.parent.postMessage({ type: 'AGILE_CHAT_STATE', isOpen: isChatOpen }, '*')
  }, [isChatOpen])

  // ── Helper: append a message to the chat history ───────────
  const appendMessage = (role, text, isError = false) => {
    setMessages((prev) => [
      ...prev,
      { id: generateId(), role, text, time: getTime(), isError },
    ])
  }

  // ── Cart Handlers (for manual drawer changes) ──────────────
  const handleUpdateQuantity = async (productId, newQty) => {
    const item = cart.find(i => i.product_id === productId);
    if (!item) return;

    if (newQty <= 0) {
      handleRemoveItem(productId)
      return
    }

    // Optimistic UI update
    setCart((prev) =>
      prev.map((i) =>
        i.product_id === productId ? { ...i, quantity: newQty } : i
      )
    )

    try {
      const updatedCart = await wcCartService.updateCartItem(item.key, newQty);
      setCart(updatedCart);
    } catch (err) {
      console.error("Failed to update quantity:", err);
      wcCartService.fetchCart().then(setCart);
    }
  }

  const handleRemoveItem = async (productId) => {
    const item = cart.find(i => i.product_id === productId);
    if (!item) return;

    // Optimistic UI update
    setCart((prev) => prev.filter((i) => i.product_id !== productId))

    try {
      const updatedCart = await wcCartService.removeCartItem(item.key);
      setCart(updatedCart);
    } catch (err) {
      console.error("Failed to remove item:", err);
      wcCartService.fetchCart().then(setCart);
    }
  }

  const handleClearCart = async () => {
    setCart([])
    try {
      const updatedCart = await wcCartService.clearCart();
      setCart(updatedCart);
    } catch (err) {
      console.error("Failed to clear cart:", err);
      wcCartService.fetchCart().then(setCart);
    }
  }

  // Add multiple items to cart (callback for the reorder button)
  const handleAddItemsToCart = async (items) => {
    for (const newItem of items) {
      try {
        await wcCartService.addToCart(newItem.product_id, newItem.quantity);
      } catch (err) {
        console.error("Failed to add to cart:", err);
      }
    }
    const updated = await wcCartService.fetchCart();
    setCart(updated);
    setIsCartOpen(true)
  }

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

      // 6. Add the AI's reply to the chat and execute any cart actions
      appendMessage('ai', response.reply)

      let currentCart = [...cart];
      if (response.cart_actions && response.cart_actions.length > 0) {
        for (const action of response.cart_actions) {
          try {
            if (action.action === "set_quantity") {
              if (action.quantity === 0) {
                const item = currentCart.find(i => i.product_id === action.product_id);
                if (item) await wcCartService.removeCartItem(item.key);
              } else {
                const item = currentCart.find(i => i.product_id === action.product_id);
                if (item) {
                  await wcCartService.updateCartItem(item.key, action.quantity);
                } else {
                  await wcCartService.addToCart(action.product_id, action.quantity);
                }
              }
            }
          } catch (err) {
            console.error("Cart action failed:", err);
          }
        }
        currentCart = await wcCartService.fetchCart();
      } else if (response.cart) {
        // Fallback in case of backend local mutator updates
        currentCart = response.cart;
      }

      // Auto-open cart drawer if items were added by the assistant
      const currentTotalQty = cart.reduce((sum, item) => sum + item.quantity, 0)
      const newTotalQty = currentCart.reduce((sum, item) => sum + item.quantity, 0)
      if (newTotalQty > currentTotalQty) {
        setIsCartOpen(true)
      }

      setCart(currentCart)
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

      let currentCart = [...cart];
      if (response.cart_actions && response.cart_actions.length > 0) {
        for (const action of response.cart_actions) {
          try {
            if (action.action === "set_quantity") {
              if (action.quantity === 0) {
                const item = currentCart.find(i => i.product_id === action.product_id);
                if (item) await wcCartService.removeCartItem(item.key);
              } else {
                const item = currentCart.find(i => i.product_id === action.product_id);
                if (item) {
                  await wcCartService.updateCartItem(item.key, action.quantity);
                } else {
                  await wcCartService.addToCart(action.product_id, action.quantity);
                }
              }
            }
          } catch (err) {
            console.error("Cart action failed:", err);
          }
        }
        currentCart = await wcCartService.fetchCart();
      } else if (response.cart) {
        currentCart = response.cart;
      }

      const currentTotalQty = cart.reduce((sum, item) => sum + item.quantity, 0)
      const newTotalQty = currentCart.reduce((sum, item) => sum + item.quantity, 0)
      if (newTotalQty > currentTotalQty) {
        setIsCartOpen(true)
      }

      setCart(currentCart)
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
    <>
      {/* Floating Chat Button */}
      {!isChatOpen && (
        <button
          className="floating-chat-button"
          onClick={() => { setIsChatOpen(true); setHasOpened(true); }}
          aria-label="Open chat"
          aria-expanded={isChatOpen}
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
        </button>
      )}

      {/* Floating Chat Window */}
      {isChatOpen && (
        <div className="floating-chat-window" aria-modal="true" role="dialog">

          <div className="app-shell">

          {/* Header */}
          <header className="app-header">
            <div className="header-brand">
              <div className="header-logo">✦</div>

            </div>

            <div style={{ display: "flex", alignItems: "center" }}>

              <button
                className="cart-toggle-btn"
                onClick={() => setIsCartOpen(true)}
              >
                🛒

                {cart.length > 0 && (
                  <span className="cart-badge-number">
                    {cart.reduce((a, b) => a + b.quantity, 0)}
                  </span>
                )}
              </button>

              {messages.length > 0 && (
                <button
                  className="clear-btn"
                  onClick={handleClear}
                >
                  Clear
                </button>
              )}

              <div className="header-status">
                <div className="status-dot" />
                <span>Online</span>
              </div>

              {/* Minimize Button moved to header */}
              <button
                className="minimize-btn"
                onClick={() => setIsChatOpen(false)}
                aria-label="Minimize chat"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
              </button>

            </div>
          </header>

          {/* Chat */}
          <main className="chat-body">

            <ChatWindow
              messages={messages}
              isLoading={isLoading}
              onSuggest={handleSuggest}
              onAddItemsToCart={handleAddItemsToCart}
            />

            <InputBar
              value={input}
              onChange={setInput}
              onSend={handleSend}
              disabled={isLoading}
            />

          </main>

          {/* Cart Drawer */}

          <CartDrawer
            isOpen={isCartOpen}
            onClose={() => setIsCartOpen(false)}
            cart={cart}
            onUpdateQuantity={handleUpdateQuantity}
            onRemove={handleRemoveItem}
            onClear={handleClearCart}
          />

        </div>

      </div>
      )}
    </>
  )
}

export default App
