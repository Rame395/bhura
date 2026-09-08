/* BHURA storefront — shared API + cart helpers. Loaded on every page. */

async function apiGet(path) {
  const res = await fetch(path, { credentials: "same-origin" });
  if (!res.ok) throw new Error(`GET ${path} failed (${res.status})`);
  return res.json();
}

async function apiJSON(method, path, body) {
  const res = await fetch(path, {
    method,
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `${method} ${path} failed (${res.status})`);
  }
  return res.json();
}

async function apiForm(method, path, formData) {
  const res = await fetch(path, { method, credentials: "same-origin", body: formData });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `${method} ${path} failed (${res.status})`);
  }
  return res.json();
}

function formatNPR(amount) {
  return `NPR ${Number(amount).toLocaleString("en-IN")}`;
}

/* ---------------- Cart ---------------- */

async function getCart() {
  return apiGet("/api/cart");
}

async function addToCart(productId, color, size, quantity = 1) {
  return apiJSON("POST", "/api/cart/items", { product_id: productId, color, size, quantity });
}

async function updateCartItem(itemId, quantity) {
  return apiJSON("PATCH", `/api/cart/items/${itemId}`, { quantity });
}

async function removeCartItem(itemId) {
  const res = await fetch(`/api/cart/items/${itemId}`, { method: "DELETE", credentials: "same-origin" });
  if (!res.ok) throw new Error("Failed to remove item");
  return res.json();
}

async function refreshCartBadge() {
  try {
    const cart = await getCart();
    document.querySelectorAll("#cart-counter").forEach((el) => {
      el.textContent = `(${cart.item_count})`;
    });
    return cart;
  } catch (e) {
    return null;
  }
}

/* ---------------- Toast ---------------- */

function showToast(message) {
  const notification = document.createElement("div");
  notification.className =
    "fixed bottom-8 right-8 left-8 sm:left-auto bg-bhuraWhite text-bhuraBlack px-6 py-4 shadow-2xl z-[60] text-xs font-semibold tracking-wider uppercase flex items-center space-x-3 transition-all duration-300 transform translate-y-4 opacity-0";
  notification.innerHTML = `<span>${message}</span>`;
  document.body.appendChild(notification);
  requestAnimationFrame(() => {
    notification.classList.remove("translate-y-4", "opacity-0");
  });
  setTimeout(() => {
    notification.classList.add("translate-y-4", "opacity-0");
    setTimeout(() => notification.remove(), 300);
  }, 2500);
}

/* ---------------- WhatsApp ordering ---------------- */

async function whatsAppOrderFromCart(cart, settings, orderNumber) {
  const phone = settings.whatsapp_number;
  let lines = [`Hello BHURA, I would like to place an order:`, ""];
  if (orderNumber) lines.push(`*Order:* #${orderNumber}`, "");
  cart.items.forEach((i) => {
    lines.push(`*${i.title}*`);
    lines.push(`Color: ${i.color} / Size: ${i.size} / Qty: ${i.quantity}`);
    lines.push(`Price: ${formatNPR(i.line_total)}`);
    lines.push("");
  });
  lines.push(`*Total:* ${formatNPR(cart.total)}`);
  lines.push("");
  lines.push("Please confirm availability and shipping details.");
  const message = encodeURIComponent(lines.join("\n"));
  window.open(`https://wa.me/${phone}?text=${message}`, "_blank");
}
