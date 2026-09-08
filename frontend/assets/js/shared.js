/* BHURA storefront — shared header/menu behavior. Loaded on every page, after api.js. */

document.addEventListener("DOMContentLoaded", () => {
  const menuToggle = document.getElementById("menu-toggle");
  const mobileMenu = document.getElementById("mobile-menu");
  if (menuToggle && mobileMenu) {
    menuToggle.addEventListener("click", () => {
      mobileMenu.classList.toggle("translate-x-full");
    });
    document.querySelectorAll(".mobile-link").forEach((link) => {
      link.addEventListener("click", () => mobileMenu.classList.add("translate-x-full"));
    });
  }

  refreshCartBadge();
  initSiteSearch();
  applySiteSettingsToPage();
  showAdminReturnLinkIfLoggedIn();
});

/* ---------------- "Back to Admin" badge (storefront pages only, admins only) ---------------- */

async function showAdminReturnLinkIfLoggedIn() {
  // This file is only loaded by storefront pages (the admin pages have their own
  // scripts), so this never runs while actually inside /admin/ — exactly where a
  // "back to admin" link would be redundant anyway.
  try {
    const res = await fetch("/api/admin/me", { credentials: "same-origin" });
    if (!res.ok) return; // not an admin session — show nothing, silently

    const badge = document.createElement("a");
    badge.href = "/admin/dashboard.html";
    badge.className =
      "fixed bottom-6 right-6 z-[80] bg-bhuraBlack text-bhuraWhite text-[11px] font-semibold uppercase tracking-widest px-4 py-3 shadow-lg hover:bg-bhuraTextGrey transition-colors flex items-center gap-2";
    badge.innerHTML = `<span>⚙</span><span>Back to Admin</span>`;
    document.body.appendChild(badge);
  } catch (e) {
    // Settings/network hiccup — fail silently, this is a convenience affordance only.
  }
}

/* ---------------- Search overlay ---------------- */

function initSiteSearch() {
  const trigger = document.getElementById("search-trigger");
  if (!trigger) return; // page doesn't have a search trigger in its header

  const overlay = document.createElement("div");
  overlay.id = "site-search-overlay";
  overlay.className = "fixed inset-0 bg-bhuraBlack/95 z-[70] hidden flex flex-col items-center px-6 pt-28";
  overlay.innerHTML = `
    <button id="site-search-close" aria-label="Close search" class="absolute top-6 right-8 text-bhuraWhite text-xl font-mono uppercase tracking-widest hover:opacity-70">✕ Close</button>
    <div class="w-full max-w-xl">
      <div class="flex gap-3 items-center border-b border-white/30 focus-within:border-white">
        <input id="site-search-input" type="text" placeholder="SEARCH PRODUCTS…"
          class="flex-1 bg-transparent text-bhuraWhite placeholder-white/40 text-lg tracking-wide py-3 focus:outline-none border-0">
        <select id="site-search-scope" class="bg-transparent text-white/60 text-[11px] uppercase tracking-widest py-3 focus:outline-none border-0 cursor-pointer">
          <option value="" class="text-black">All</option>
          <option value="men" class="text-black">Men</option>
          <option value="women" class="text-black">Women</option>
          <option value="Shoes" class="text-black">Shoes</option>
          <option value="Clothing" class="text-black">Clothing</option>
          <option value="Accessories" class="text-black">Accessories</option>
          <option value="Sports" class="text-black">Sports</option>
        </select>
      </div>
      <div id="site-search-results" class="mt-6 space-y-1 max-h-[60vh] overflow-y-auto"></div>
    </div>
  `;
  document.body.appendChild(overlay);

  const input = overlay.querySelector("#site-search-input");
  const scope = overlay.querySelector("#site-search-scope");
  const results = overlay.querySelector("#site-search-results");
  const closeBtn = overlay.querySelector("#site-search-close");

  function openOverlay() {
    overlay.classList.remove("hidden");
    setTimeout(() => input.focus(), 50);
  }
  function closeOverlay() {
    overlay.classList.add("hidden");
    input.value = "";
    scope.value = "";
    results.innerHTML = "";
  }

  trigger.addEventListener("click", openOverlay);
  closeBtn.addEventListener("click", closeOverlay);
  overlay.addEventListener("click", (e) => { if (e.target === overlay) closeOverlay(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeOverlay(); });

  let debounceTimer;
  input.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    const q = input.value.trim();
    if (!q && !scope.value) { results.innerHTML = ""; return; }
    debounceTimer = setTimeout(() => runSearch(q), 250);
  });
  scope.addEventListener("change", () => {
    const q = input.value.trim();
    if (!q && !scope.value) { results.innerHTML = ""; return; }
    runSearch(q);
  });

  const GENDER_SCOPES = new Set(["men", "women"]);

  async function runSearch(q) {
    results.innerHTML = `<p class="text-white/40 text-xs uppercase tracking-widest py-4">Searching…</p>`;
    try {
      const params = new URLSearchParams();
      if (q) params.set("search", q);
      const scopeValue = scope.value;
      if (scopeValue) {
        if (GENDER_SCOPES.has(scopeValue)) params.set("category", scopeValue);
        else params.set("department", scopeValue);
      }
      const products = await apiGet(`/api/products?${params.toString()}`);
      if (!products.length) {
        const what = q ? `"${q}"` : (scope.options[scope.selectedIndex]?.textContent || "this category");
        results.innerHTML = `<p class="text-white/40 text-xs uppercase tracking-widest py-4">No products match ${what}.</p>`;
        return;
      }
      const cardHtml = (p) => `
        <a href="product.html?slug=${p.slug}" class="flex items-center gap-4 py-3 border-b border-white/10 hover:bg-white/5 px-2 -mx-2 transition-colors">
          <div class="w-12 h-16 bg-white/10 overflow-hidden flex-shrink-0">
            ${p.primary_image ? `<img src="${p.primary_image}" class="w-full h-full object-cover">` : ""}
          </div>
          <div class="flex-1 text-left">
            <p class="text-bhuraWhite text-sm uppercase tracking-wide">${p.title}</p>
            <p class="text-white/40 text-[11px] uppercase">${p.subcategory || ""}</p>
          </div>
          <span class="text-bhuraWhite text-xs font-semibold">${formatNPR(p.price)}</span>
        </a>`;
      // Browsing a scope with no text query: show every matching item (that's the
      // whole point of picking "Men"/"Shoes" etc). An active text search still caps
      // at a shortlist, since it's meant as a quick jump-to-product, not a full browse.
      const shown = q ? products.slice(0, 8) : products;
      results.innerHTML = shown.map(cardHtml).join("");
    } catch (e) {
      results.innerHTML = `<p class="text-white/40 text-xs uppercase tracking-widest py-4">Search unavailable right now.</p>`;
    }
  }
}

/* ---------------- Settings-driven footer / contact / social ---------------- */

async function applySiteSettingsToPage() {
  const contactEls = document.querySelectorAll("[data-contact-phone]");
  const igEls = document.querySelectorAll("[data-social='instagram']");
  const ttEls = document.querySelectorAll("[data-social='tiktok']");
  if (!contactEls.length && !igEls.length && !ttEls.length) return;

  try {
    const settings = await apiGet("/api/settings");

    contactEls.forEach((el) => {
      if (settings.contact_phone) {
        el.textContent = `Contact — ${settings.contact_phone}`;
        el.href = `https://wa.me/${settings.contact_phone.replace(/\D/g, "")}`;
        el.target = "_blank";
      }
    });

    igEls.forEach((el) => {
      if (settings.instagram_url) {
        el.href = settings.instagram_url;
        el.target = "_blank";
        el.rel = "noopener";
      } else {
        el.classList.add("opacity-40", "pointer-events-none");
      }
    });

    ttEls.forEach((el) => {
      if (settings.tiktok_url) {
        el.href = settings.tiktok_url;
        el.target = "_blank";
        el.rel = "noopener";
      } else {
        el.classList.add("opacity-40", "pointer-events-none");
      }
    });
  } catch (e) {
    // Settings unavailable — leave the placeholder links as-is rather than break the page.
  }
}

/* ---------------- WhatsApp order -> real trackable order ---------------- */

function promptWhatsAppContact() {
  return new Promise((resolve) => {
    const overlay = document.createElement("div");
    overlay.className = "fixed inset-0 bg-bhuraBlack/90 z-[90] flex items-center justify-center px-6";
    overlay.innerHTML = `
      <div class="bg-bhuraWhite text-bhuraBlack w-full max-w-sm p-7 space-y-4">
        <h3 class="text-sm font-black uppercase tracking-widest">Before we open WhatsApp</h3>
        <p class="text-[11px] text-bhuraTextGrey uppercase tracking-wider leading-relaxed">
          Just your name and number, so we can find this order when you message us — everything else gets sorted over chat.
        </p>
        <div>
          <label class="block text-[10px] font-mono uppercase tracking-widest text-bhuraTextGrey mb-1">Full Name</label>
          <input id="wa-contact-name" type="text" required placeholder="YOUR NAME" class="w-full bg-transparent border border-bhuraLightGrey px-4 py-3 text-xs tracking-widest focus:outline-none focus:border-bhuraBlack">
        </div>
        <div>
          <label class="block text-[10px] font-mono uppercase tracking-widest text-bhuraTextGrey mb-1">Phone Number</label>
          <input id="wa-contact-phone" type="tel" required placeholder="98XXXXXXXX" class="w-full bg-transparent border border-bhuraLightGrey px-4 py-3 text-xs tracking-widest focus:outline-none focus:border-bhuraBlack">
        </div>
        <p id="wa-contact-error" class="hidden text-[11px] text-red-600 uppercase tracking-wider"></p>
        <div class="flex gap-2 pt-1">
          <button id="wa-contact-cancel" class="flex-1 border border-bhuraLightGrey text-bhuraBlack py-3 text-[11px] font-semibold uppercase tracking-widest hover:bg-bhuraLightGrey transition-colors">Cancel</button>
          <button id="wa-contact-continue" class="flex-1 bg-[#25D366] text-white py-3 text-[11px] font-semibold uppercase tracking-widest hover:opacity-90 transition-opacity">Continue</button>
        </div>
      </div>`;
    document.body.appendChild(overlay);

    const cleanup = (result) => { overlay.remove(); resolve(result); };
    overlay.querySelector("#wa-contact-cancel").addEventListener("click", () => cleanup(null));
    overlay.addEventListener("click", (e) => { if (e.target === overlay) cleanup(null); });
    overlay.querySelector("#wa-contact-continue").addEventListener("click", () => {
      const name = overlay.querySelector("#wa-contact-name").value.trim();
      const phone = overlay.querySelector("#wa-contact-phone").value.trim();
      const errorEl = overlay.querySelector("#wa-contact-error");
      if (!name || !phone) {
        errorEl.textContent = "Please fill in both your name and phone number.";
        errorEl.classList.remove("hidden");
        return;
      }
      const parts = name.split(" ");
      cleanup({ first_name: parts[0], last_name: parts.slice(1).join(" ") || parts[0], phone });
    });
  });
}

async function createWhatsAppOrder(contact) {
  const fd = new FormData();
  fd.append("first_name", contact.first_name);
  fd.append("last_name", contact.last_name);
  fd.append("phone", contact.phone);
  fd.append("payment_method", "whatsapp");
  return apiForm("POST", "/api/orders", fd);
}

/* ---------------- Mega menu (Men / Women category dropdown) ---------------- */

function injectMegaMenuStyles() {
  const style = document.createElement('style');
  style.textContent = `
    .mega-menu-panel {
      position: fixed; top: 80px; left: 0; right: 0; z-index: 45;
      background: #FFFFFF; color: #111111;
      border-bottom: 1px solid #EAEAEA;
      box-shadow: 0 12px 24px -8px rgba(0,0,0,0.15);
      opacity: 0; visibility: hidden; transform: translateY(-8px);
      transition: opacity .2s ease, transform .2s ease, visibility .2s;
    }
    .mega-menu-panel.open { opacity: 1; visibility: visible; transform: translateY(0); }
  `;
  document.head.appendChild(style);
}

function initMegaMenu() {
  injectMegaMenuStyles();
  const taxonomyCache = {};

  async function getTaxonomy(gender) {
    if (!taxonomyCache[gender]) {
      try {
        taxonomyCache[gender] = await apiGet(`/api/products/taxonomy?category=${gender}`);
      } catch (e) {
        taxonomyCache[gender] = {};
      }
    }
    return taxonomyCache[gender];
  }

  function panelHtml(gender, taxonomy) {
    const departments = Object.keys(taxonomy);
    if (!departments.length) {
      return `<p class="text-xs text-bhuraTextGrey uppercase tracking-widest py-8 text-center">No products yet.</p>`;
    }
    const columns = departments.map((dept) => `
      <div>
        <a href="${gender}.html?department=${encodeURIComponent(dept)}" class="block text-xs font-bold uppercase tracking-widest text-bhuraBlack hover:opacity-60 mb-3">${dept}</a>
        <ul class="space-y-2">
          ${taxonomy[dept].map((sub) => `
            <li><a href="${gender}.html?department=${encodeURIComponent(dept)}&subcategory=${encodeURIComponent(sub)}" class="text-xs font-medium text-bhuraBlack hover:opacity-60 transition-opacity">${sub}</a></li>
          `).join('')}
        </ul>
      </div>`).join('');
    return `<div class="grid grid-cols-2 sm:grid-cols-4 gap-8">${columns}</div>`;
  }

  function buildPanel(gender) {
    const panel = document.createElement('div');
    panel.className = 'mega-menu-panel';
    panel.dataset.gender = gender;
    panel.innerHTML = `<div class="max-w-[1440px] mx-auto px-6 lg:px-12 py-10 overflow-y-auto" style="max-height: 50vh;">
      <p class="text-xs text-bhuraTextGrey uppercase tracking-widest py-8 text-center">Loading…</p>
    </div>`;
    document.body.appendChild(panel);
    return panel;
  }

  function closeAllPanels() {
    document.querySelectorAll('.mega-menu-panel').forEach((p) => p.classList.remove('open'));
  }

  async function openPanel(gender, panel) {
    closeAllPanels();
    panel.classList.add('open');
    const taxonomy = await getTaxonomy(gender);
    panel.querySelector('div').innerHTML = panelHtml(gender, taxonomy);
  }

  ['men', 'women'].forEach((gender) => {
    const trigger = document.querySelector(`header nav a[href="${gender}.html"]`);
    if (!trigger) return; // this page's header doesn't have this link (e.g. gallery's "The Story" variant) — skip quietly

    const panel = buildPanel(gender);
    let closeTimer;
    const cancelClose = () => clearTimeout(closeTimer);
    const scheduleClose = () => { closeTimer = setTimeout(() => panel.classList.remove('open'), 200); };

    trigger.addEventListener('mouseenter', () => { cancelClose(); openPanel(gender, panel); });
    trigger.addEventListener('click', (e) => {
      if (panel.classList.contains('open')) return; // let the click through to navigate
      e.preventDefault();
      openPanel(gender, panel);
    });
    trigger.addEventListener('mouseleave', scheduleClose);
    panel.addEventListener('mouseenter', cancelClose);
    panel.addEventListener('mouseleave', scheduleClose);
  });

  document.addEventListener('click', (e) => {
    if (!e.target.closest('.mega-menu-panel') && !e.target.closest('header nav a[href="men.html"]') && !e.target.closest('header nav a[href="women.html"]')) {
      closeAllPanels();
    }
  });
}

document.addEventListener('DOMContentLoaded', initMegaMenu);
