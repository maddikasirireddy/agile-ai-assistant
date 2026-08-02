// components/CartDrawer.jsx
// ─────────────────────────────────────────────────────────────
// Side sliding drawer showing current shopping cart items,
// subtotals, and a checkout button.
// ─────────────────────────────────────────────────────────────

import React from 'react'
import './CartDrawer.css'

/**
 * CartDrawer Component
 * @param {Object} props
 * @param {boolean} props.isOpen
 * @param {Function} props.onClose
 * @param {Array} props.cart - [{"product_id": int, "name": str, "price": float, "quantity": int, "image": str}]
 * @param {Function} props.onUpdateQuantity
 * @param {Function} props.onRemove
 * @param {Function} props.onClear
 */
const CartDrawer = ({ isOpen, onClose, cart, onUpdateQuantity, onRemove, onClear }) => {
  const subtotal = cart.reduce((sum, item) => sum + item.price * item.quantity, 0)

  const handleCheckout = () => {
    if (cart.length === 0) return
    // Proceed directly to the WooCommerce checkout! 
    // The PHP session cart is already synced via the Store API.
    const checkoutUrl = `https://agilewellness.in/checkout/`
    window.open(checkoutUrl, '_blank', 'noopener,noreferrer')
  }

  return (
    <>
      {/* Backdrop overlay */}
      {isOpen && <div className="cart-backdrop" onClick={onClose} aria-hidden="true" />}

      {/* Slideout panel */}
      <div className={`cart-drawer ${isOpen ? 'open' : ''}`} role="dialog" aria-modal="true" aria-label="Shopping Cart">
        {/* Drawer Header */}
        <div className="cart-header">
          <div className="cart-header-title">
            <span className="cart-icon">🛒</span>
            <h2>Your Cart</h2>
            <span className="cart-count-badge">{cart.reduce((a, b) => a + b.quantity, 0)}</span>
          </div>
          <button className="cart-close-btn" onClick={onClose} aria-label="Close cart">
            ✕
          </button>
        </div>

        {/* Drawer Body / Items List */}
        <div className="cart-body">
          {cart.length === 0 ? (
            <div className="cart-empty-state">
              <div className="empty-icon">🛒</div>
              <h3>Your cart is empty</h3>
              <p>Ask the shopping assistant to recommend products or add items to your cart!</p>
              <button className="shop-suggest-btn" onClick={onClose}>
                Continue Browsing
              </button>
            </div>
          ) : (
            <div className="cart-items-list">
              {cart.map((item) => (
                <div key={item.product_id} className="cart-item">
                  {/* Product thumbnail */}
                  <div className="cart-item-image">
                    {item.image ? (
                      <img src={item.image} alt={item.name} />
                    ) : (
                      <div className="placeholder-thumb">✦</div>
                    )}
                  </div>

                  {/* Product details */}
                  <div className="cart-item-details">
                    <h4 className="cart-item-name">{item.name}</h4>
                    <div className="cart-item-price">₹{item.price}</div>
                    
                    {/* Quantity selectors */}
                    <div className="cart-qty-wrapper">
                      <button
                        className="qty-btn"
                        onClick={() => onUpdateQuantity(item.product_id, item.quantity - 1)}
                        aria-label="Decrease quantity"
                      >
                        –
                      </button>
                      <span className="qty-val">{item.quantity}</span>
                      <button
                        className="qty-btn"
                        onClick={() => onUpdateQuantity(item.product_id, item.quantity + 1)}
                        aria-label="Increase quantity"
                      >
                        +
                      </button>
                    </div>
                  </div>

                  {/* Remove button */}
                  <button
                    className="cart-remove-btn"
                    onClick={() => onRemove(item.product_id)}
                    title="Remove item"
                    aria-label={`Remove ${item.name} from cart`}
                  >
                    🗑️
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Drawer Footer / Checkout Summary */}
        {cart.length > 0 && (
          <div className="cart-footer">
            <div className="cart-totals">
              <div className="cart-total-row">
                <span>Subtotal</span>
                <span>₹{subtotal.toFixed(2)}</span>
              </div>
              <div className="cart-total-row final">
                <span>Total</span>
                <span>₹{subtotal.toFixed(2)}</span>
              </div>
            </div>

            <div className="cart-actions">
              <button className="clear-cart-btn" onClick={onClear}>
                Clear Cart
              </button>
              <button className="checkout-btn" onClick={handleCheckout}>
                Proceed to Checkout
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  )
}

export default CartDrawer
