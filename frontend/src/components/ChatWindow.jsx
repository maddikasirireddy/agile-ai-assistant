// components/ChatWindow.jsx
// ─────────────────────────────────────────────────────────────
// Scrollable area that lists all messages in the conversation.
// Auto-scrolls to the latest message whenever messages change.
// Also shows a welcome screen when no messages exist yet.
// ─────────────────────────────────────────────────────────────

import React, { useEffect, useRef } from 'react'
import MessageBubble from './MessageBubble.jsx'
import TypingIndicator from './TypingIndicator.jsx'
import './ChatWindow.css'

// Suggested prompts shown on the welcome screen
const SUGGESTIONS = [
  '🌿 Show me neem products',
  '❤️ Recommend products for oily skin',
  '📦 Track my order',
  '🔄 Reorder my last package',
]

/**
 * ChatWindow Component
 * @param {Object}   props
 * @param {Array}    props.messages       — array of { id, role, text, time, isError }
 * @param {boolean}  props.isLoading      — true while waiting for AI reply
 * @param {Function} props.onSuggest      — called when user clicks a suggestion chip
 * @param {Function} props.onAddItemsToCart — callback to add multiple products to cart
 */
const ChatWindow = ({ messages, isLoading, onSuggest, onAddItemsToCart }) => {
  const containerRef = useRef(null)

  // Scroll to bottom whenever messages or loading state changes
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [messages, isLoading])

  return (
    <div className="chat-window" ref={containerRef} role="log" aria-live="polite" aria-label="Chat conversation">

      {/* ── Welcome screen — shown only when no messages exist ── */}
      {messages.length === 0 && !isLoading && (
        <div className="welcome-state">
          <div className="welcome-icon">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
          </div>
          <h2>Welcome to Agile Wellness AI</h2>
          <p>I am your shopping and wellness assistant. Ask me to recommend products, track your packages, show your order history, or reorder previous purchases.</p>

          {/* Suggestion chips to help users get started */}
          <div className="suggestion-chips">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                className="chip"
                onClick={() => onSuggest(s)}
                aria-label={`Ask: ${s}`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── Message list ── */}
      {messages.map((msg) => (
        <MessageBubble
          key={msg.id}
          role={msg.role}
          text={msg.text}
          time={msg.time}
          isError={msg.isError}
          onAddItemsToCart={onAddItemsToCart}
        />
      ))}

      {/* ── Typing indicator — shown while AI is generating a reply ── */}
      {isLoading && <TypingIndicator />}

    </div>
  )
}

export default ChatWindow
