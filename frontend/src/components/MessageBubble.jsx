// components/MessageBubble.jsx
// ─────────────────────────────────────────────────────────────
// Renders a single chat message bubble.
// Supports: **bold**, *italic*, ### headings, [text](url) links,
// | markdown tables |, ⚠️ offline warning banners,
// AND structured JSON orders / reorders.
// ─────────────────────────────────────────────────────────────

import React from 'react'
import './MessageBubble.css'

/**
 * Parse and render an inline segment of text.
 * Handles: **bold**, *italic*, [text](url)
 */
const renderInline = (text, keyPrefix = '') => {
  if (!text) return null
  // Match **bold**, *italic*, [text](url)
  const tokenRegex = /(\*\*.*?\*\*|\*[^*]+?\*|\[.*?\]\(.*?\))/g
  const parts = text.split(tokenRegex)

  return parts.map((part, i) => {
    const key = `${keyPrefix}-${i}`
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={key}>{part.slice(2, -2)}</strong>
    }
    if (part.startsWith('*') && part.endsWith('*') && part.length > 2) {
      return <em key={key}>{part.slice(1, -1)}</em>
    }
    if (part.startsWith('[') && part.includes('](') && part.endsWith(')')) {
      const closeBracket = part.indexOf('](')
      const linkText = part.slice(1, closeBracket)
      const url = part.slice(closeBracket + 2, -1)
      return (
        <a key={key} href={url} target="_top" className="chat-link">
          {linkText}
        </a>
      )
    }
    return <React.Fragment key={key}>{part}</React.Fragment>
  })
}

/**
 * Parse markdown table string into rows.
 */
const parseTable = (lines) => {
  if (lines.length < 3) return null
  const isSeparator = (line) => /^\|[\s\-:|]+\|$/.test(line.trim())
  if (!isSeparator(lines[1])) return null

  const parseRow = (line) =>
    line
      .trim()
      .replace(/^\|/, '')
      .replace(/\|$/, '')
      .split('|')
      .map((cell) => cell.trim())

  const headers = parseRow(lines[0])
  const rows = lines.slice(2).map(parseRow)
  return { headers, rows }
}

/**
 * Render full markdown message content
 */
const renderMarkdown = (text) => {
  if (!text) return null

  const lines = text.split('\n')
  const output = []
  let i = 0

  while (i < lines.length) {
    const line = lines[i]
    const trimmed = line.trim()

    // ── Offline warning banner ────────────────────────────────
    if (trimmed.startsWith('⚠️')) {
      const cleanWarning = trimmed.replace(/\*/g, '')
      output.push(
        <div key={`warn-${i}`} className="offline-banner">
          {cleanWarning}
        </div>
      )
      i++
      continue
    }

    // ── ### Heading ──────────────────────────────────────────
    if (trimmed.startsWith('### ')) {
      output.push(
        <h3 key={`h3-${i}`} className="msg-heading">
          {renderInline(trimmed.slice(4), `h3-${i}`)}
        </h3>
      )
      i++
      continue
    }

    if (trimmed.startsWith('## ')) {
      output.push(
        <h4 key={`h2-${i}`} className="msg-subheading">
          {renderInline(trimmed.slice(3), `h2-${i}`)}
        </h4>
      )
      i++
      continue
    }

    // ── Markdown table ───────────────────────────────────────
    if (trimmed.startsWith('|')) {
      const tableLines = []
      while (i < lines.length && lines[i].trim().startsWith('|')) {
        tableLines.push(lines[i])
        i++
      }
      const table = parseTable(tableLines)
      if (table) {
        output.push(
          <div key={`tbl-${i}`} className="msg-table-wrapper">
            <table className="msg-table">
              <thead>
                <tr>
                  {table.headers.map((h, hi) => (
                    <th key={hi}>{renderInline(h, `th-${hi}`)}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {table.rows.map((row, ri) => (
                  <tr key={ri}>
                    {row.map((cell, ci) => (
                      <td key={ci}>{renderInline(cell, `td-${ri}-${ci}`)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      } else {
        tableLines.forEach((tl, tli) => {
          output.push(<p key={`tl-${i}-${tli}`}>{renderInline(tl, `tl-${i}-${tli}`)}</p>)
        })
      }
      continue
    }

    // ── Bullet list item ─────────────────────────────────────
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      const listItems = []
      while (
        i < lines.length &&
        (lines[i].trim().startsWith('- ') || lines[i].trim().startsWith('* '))
      ) {
        const content = lines[i].trim().slice(2)
        listItems.push(
          <li key={i}>
            {renderInline(content, `li-${i}`)}
          </li>
        )
        i++
      }
      output.push(
        <ul key={`ul-${i}`} className="msg-list">
          {listItems}
        </ul>
      )
      continue
    }

    // ── Empty line ───────────────────────────────────────────
    if (trimmed === '') {
      output.push(<div key={`sp-${i}`} className="msg-spacer" />)
      i++
      continue
    }

    // ── Paragraph ────────────────────────────────────────────
    output.push(
      <p key={`p-${i}`} className="msg-para">
        {renderInline(trimmed, `p-${i}`)}
      </p>
    )
    i++
  }

  return output
}

/**
 * MessageBubble Component
 * @param {'user'|'ai'} role
 * @param {string}      text
 * @param {string}      time
 * @param {boolean}     isError
 * @param {Function}    onAddItemsToCart
 */
const MessageBubble = ({ role, text, time, isError, onAddItemsToCart }) => {
  const avatar = role === 'ai' ? '✦' : 'U'

  // Detect if text is a structural JSON payload
  let isJson = false
  let parsedData = null
  try {
    const trimmed = text.trim()
    if (trimmed.startsWith('{') && trimmed.endsWith('}')) {
      parsedData = JSON.parse(trimmed)
      if (parsedData && parsedData.type) {
        isJson = true
      }
    }
  } catch (e) {}

  return (
    <div className={`message-row ${role}`}>
      <div className="avatar" aria-hidden="true">{avatar}</div>

      <div>
        <div className={`bubble ${isError ? 'error' : ''} ${isJson ? 'json-bubble' : ''}`}>
          {isJson ? (
            parsedData.type === 'order_history' ? (
              <div className="order-history-container">
                <h4 className="order-section-title">📋 Your Order History</h4>
                {parsedData.orders.length === 0 ? (
                  <p className="no-orders-msg">You don't have any previous orders yet.</p>
                ) : (
                  <div className="orders-grid">
                    {parsedData.orders.map((order) => (
                      <div key={order.id} className="order-summary-card">
                        <div className="order-summary-header">
                          <span className="order-id">Order #{order.id}</span>
                          <span className="order-date">{order.date}</span>
                        </div>
                        <div className="order-summary-details">
                          <div className="summary-row">
                            <span className="label">Status:</span>
                            <span className={`val status-pill ${order.status}`}>{order.status.toUpperCase()}</span>
                          </div>
                          <div className="summary-row">
                            <span className="label">Payment:</span>
                            <span className={`val payment-pill ${order.payment_status}`}>{order.payment_status.toUpperCase()}</span>
                          </div>
                          <div className="summary-row total-row">
                            <span className="label">Total:</span>
                            <span className="val price-text">{order.currency} {order.total}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : parsedData.type === 'reorder' ? (
              <div className="reorder-container">
                <h4 className="order-section-title">🔄 Reorder Last Purchase</h4>
                {parsedData.error ? (
                  <p className="no-orders-msg">{parsedData.error}</p>
                ) : (
                  <div>
                    <div className="reorder-items-list">
                      {parsedData.items.map((item) => (
                        <div key={item.product_id} className="reorder-product-row">
                          {item.image ? (
                            <img src={item.image} alt={item.name} className="reorder-product-thumb" />
                          ) : (
                            <div className="placeholder-thumb">✦</div>
                          )}
                          <div className="reorder-product-info">
                            <span className="reorder-product-name">{item.name}</span>
                            <span className="reorder-product-meta">Qty: {item.quantity} × ₹{item.price % 1 === 0 ? item.price.toFixed(0) : item.price.toFixed(2)}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                    <button 
                      className="reorder-submit-btn"
                      onClick={() => onAddItemsToCart(parsedData.items)}
                    >
                      🛒 Add All to Cart
                    </button>
                  </div>
                )}
              </div>
            ) : (
              renderMarkdown(text)
            )
          ) : (
            role === 'ai' ? renderMarkdown(text) : <p className="msg-para">{text}</p>
          )}
        </div>
        {time && <div className="timestamp">{time}</div>}
      </div>
    </div>
  )
}

export default MessageBubble
