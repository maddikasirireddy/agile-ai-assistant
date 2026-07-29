// components/InputBar.jsx
// ─────────────────────────────────────────────────────────────
// The bottom input area with a growing textarea and Send button.
// - Pressing Enter sends the message
// - Shift+Enter adds a newline
// - Textarea auto-grows up to 140px, then scrolls
// ─────────────────────────────────────────────────────────────

import React, { useRef, useEffect } from 'react'
import './InputBar.css'

/**
 * InputBar Component
 * @param {Object}   props
 * @param {string}   props.value      — current text in the input
 * @param {Function} props.onChange   — updates value in parent state
 * @param {Function} props.onSend     — triggers when user sends a message
 * @param {boolean}  props.disabled   — disables input while AI is responding
 */
const InputBar = ({ value, onChange, onSend, disabled }) => {
  const textareaRef = useRef(null)

  // Auto-resize the textarea height based on its content
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'                        // reset first
    el.style.height = `${el.scrollHeight}px`        // grow to content
  }, [value])

  // Handle keyboard shortcut: Enter = send, Shift+Enter = newline
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()   // prevent default newline
      onSend()             // trigger send
    }
  }

  return (
    <div className="input-bar">
      {/* Auto-growing textarea */}
      <textarea
        ref={textareaRef}
        id="chat-input"
        rows={1}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Search products, ask questions, track orders…"
        disabled={disabled}
        aria-label="Type your message"
        aria-multiline="true"
      />

      {/* Keyboard hint shown to the right of textarea */}
      <span className="input-hint">Enter ↵</span>

      {/* Send button with an inline SVG arrow icon */}
      <button
        id="send-button"
        className="send-btn"
        onClick={onSend}
        disabled={disabled || !value.trim()}
        aria-label="Send message"
        title="Send message"
      >
        {/* Paper-plane / send arrow SVG */}
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2"
             strokeLinecap="round" strokeLinejoin="round">
          <line x1="22" y1="2" x2="11" y2="13" />
          <polygon points="22 2 15 22 11 13 2 9 22 2" />
        </svg>
      </button>
    </div>
  )
}

export default InputBar
