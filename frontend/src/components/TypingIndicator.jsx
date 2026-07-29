// components/TypingIndicator.jsx
// ─────────────────────────────────────────────────────────────
// Shows an animated three-dot loader while waiting for AI reply.
// Displayed on the LEFT side (same as AI messages).
// ─────────────────────────────────────────────────────────────

import React from 'react'
import './TypingIndicator.css'

const TypingIndicator = () => {
  return (
    // aria-label makes it accessible for screen readers
    <div className="typing-indicator" aria-label="AI is typing">
      <span></span>
      <span></span>
      <span></span>
    </div>
  )
}

export default TypingIndicator
