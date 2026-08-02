/**
 * WooCommerce Store API Cart Service
 * Connects directly to WooCommerce /wp-json/wc/store/v1/cart endpoint
 */

const STORE_API = 'https://agilewellness.in/wp-json/wc/store/v1/cart';

let cachedNonce = sessionStorage.getItem('wc_nonce') || '';
let cachedCartToken = sessionStorage.getItem('wc_cart_token') || '';

const getHeaders = () => {
  const headers = { 'Content-Type': 'application/json' };
  if (cachedNonce) headers['Nonce'] = cachedNonce;
  if (cachedCartToken) headers['Cart-Token'] = cachedCartToken;
  return headers;
};

const captureHeaders = (res) => {
  const nonce = res.headers.get('Nonce');
  const token = res.headers.get('Cart-Token');
  if (nonce) {
    cachedNonce = nonce;
    sessionStorage.setItem('wc_nonce', nonce);
  }
  if (token) {
    cachedCartToken = token;
    sessionStorage.setItem('wc_cart_token', token);
  }
};

const mapWcCartToLocal = (wcCartData) => {
  if (!wcCartData || !wcCartData.items) return [];
  return wcCartData.items.map(item => ({
    key: item.key,
    product_id: item.id,
    name: item.name,
    price: item.prices.price,
    quantity: item.quantity,
    image: item.images && item.images.length > 0 ? item.images[0].src : ''
  }));
};

export const fetchCart = async () => {
  const res = await fetch(STORE_API, { 
    headers: getHeaders(),
    credentials: "include"
  });
  captureHeaders(res);
  if (!res.ok) throw new Error(`Failed to fetch cart from WooCommerce (${res.status} ${res.statusText})`);
  const data = await res.json();
  return mapWcCartToLocal(data);
};

export const addToCart = async (productId, quantity = 1) => {
  if (!cachedNonce) await fetchCart();
  const res = await fetch(`${STORE_API}/items`, {
    method: 'POST',
    headers: getHeaders(),
    credentials: "include",
    body: JSON.stringify({ id: productId, quantity })
  });
  captureHeaders(res);
  if (!res.ok) throw new Error(`Failed to add item to WooCommerce cart (${res.status} ${res.statusText})`);
  const data = await res.json();
  return mapWcCartToLocal(data);
};

export const updateCartItem = async (key, quantity) => {
  if (!cachedNonce) await fetchCart();
  const res = await fetch(`${STORE_API}/items/${key}`, {
    method: 'PUT',
    headers: getHeaders(),
    credentials: "include",
    body: JSON.stringify({ quantity })
  });
  captureHeaders(res);
  if (!res.ok) throw new Error(`Failed to update item in WooCommerce cart (${res.status} ${res.statusText})`);
  const data = await res.json();
  return mapWcCartToLocal(data);
};

export const removeCartItem = async (key) => {
  if (!cachedNonce) await fetchCart();
  const res = await fetch(`${STORE_API}/items/${key}`, {
    method: 'DELETE',
    headers: getHeaders(),
    credentials: "include"
  });
  captureHeaders(res);
  if (!res.ok) throw new Error(`Failed to remove item from WooCommerce cart (${res.status} ${res.statusText})`);
  const data = await res.json();
  return mapWcCartToLocal(data);
};

export const clearCart = async () => {
  const cart = await fetchCart();
  for (const item of cart) {
    await removeCartItem(item.key);
  }
  return [];
};
