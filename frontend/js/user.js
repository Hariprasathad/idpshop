// 🔐 Authentication Check
const user = checkAuth();
if (!user) {
    window.location.href = '../auth/login.html';
}

let allProducts = [];
let wishlistIds = new Set();
let currentLastKey = null;

function generateStars(rating) {
    const r = Math.floor(rating || 0);
    let stars = "";
    for (let i = 1; i <= 5; i++) {
        if (i <= r) {
            stars += '<i class="fa-solid fa-star"></i>';
        } else {
            stars += '<i class="fa-regular fa-star"></i>';
        }
    }
    return stars;
}

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', async () => {
    updateProfileUI();
    await syncWishlist();
    loadProducts();

    // 🔍 Backend Search Logic
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            const query = e.target.value.trim();
            
            debounceTimer = setTimeout(() => {
                if (query.length === 0) {
                    loadProducts();
                } else if (query.length >= 2) {
                    loadProducts(query);
                }
            }, 500); // Debounce for 500ms
        });
    }
});

async function syncWishlist() {
    try {
        const data = await apiCall('wishlist');
        const items = data.products || [];
        wishlistIds = new Set(items.map(i => i.productId));
    } catch (err) {
        console.error("Sync Wishlist Error:", err);
    }
}

// Update Profile info in Navbar/Tab
function updateProfileUI() {
    const initial = user.name.charAt(0).toUpperCase();
    const avatar = document.getElementById('userInitial');
    if (avatar) avatar.innerText = initial;
    
    const welcomeName = document.getElementById('welcomeName');
    if (welcomeName) welcomeName.innerText = user.name;
    
    // Tab Fields
    const pName = document.getElementById('profileName');
    const pEmail = document.getElementById('profileEmail');
    const pPhone = document.getElementById('profilePhone');
    const pAddress = document.getElementById('profileAddress');
    const pCity = document.getElementById('profileCity');
    const pState = document.getElementById('profileState');
    const pPincode = document.getElementById('profilePincode');

    if (pName) pName.innerText = user.name;
    if (pEmail) pEmail.innerText = user.email;
    if (pPhone) pPhone.innerText = user.phone || '-';
    if (pAddress) pAddress.innerText = user.addressLine || '-';
    if (pCity) pCity.innerText = user.city || '-';
    if (pState) pState.innerText = user.state || '-';
    if (pPincode) pPincode.innerText = user.pincode || '-';
}

function editProfile() {
    window.location.href = 'edit-profile.html';
}

// 📦 Load Products from API (Unified for Normal & Search Pagination)
async function loadProducts(search = "", isLoadMore = false) {
    const grid = document.getElementById('productGrid');
    if (!isLoadMore) {
        currentLastKey = null; // Reset pagination
        grid.innerHTML = '<div class="loading">Loading products...</div>';
    }

    const btn = document.getElementById('loadMoreBtn');
    if (isLoadMore && btn) {
        btn.innerText = "Loading...";
        btn.disabled = true;
    }

    try {
        const params = { limit: 8 };
        if (search) {
            params.q = search;
        }
        if (isLoadMore && currentLastKey) {
            params.lastKey = currentLastKey;
        }

        const data = await apiCall('products', 'GET', null, params);
        const newProducts = data.products || [];

        if (isLoadMore) {
            allProducts = [...allProducts, ...newProducts];
            renderProducts(newProducts, 'productGrid', true);
        } else {
            allProducts = newProducts;
            renderProducts(allProducts);
        }

        currentLastKey = data.lastKey;
        togglePaginationBtn();
    } catch (err) {
        console.error("Load Products Error:", err);
    } finally {
        if (isLoadMore && btn) {
            btn.innerText = "Load More Products";
            btn.disabled = false;
        }
    }
}

async function loadMoreProducts() {
    const searchInput = document.getElementById('searchInput');
    const query = searchInput ? searchInput.value.trim() : "";
    const searchQuery = query.length >= 2 ? query : "";
    await loadProducts(searchQuery, true);
}

function togglePaginationBtn() {
    const container = document.getElementById('paginationContainer');
    if (container) {
        container.style.display = currentLastKey ? 'block' : 'none';
    }
}

const PLACEHOLDER = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMDAiIGhlaWdodD0iMTAwIiB2aWV3Qm94PSIwIDAgMTAwIDEwMCI+PHJlY3Qgd2lkdGg9IjEwMCIgaGVpZ2h0PSIxMDAiIGZpbGw9IiNmMWY1ZjkiLz48dGV4dCB4PSI1MCUiIHk9IjUwJSIgZG9taW5hbnQtYmFzZWxpbmU9Im1pZGRsZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTAiIGZpbGw9IiM5NGEzYjgiPk5vIEltYWdlPC90ZXh0Pjwvc3ZnPg==';

// 🖼️ Render Product Grid
function renderProducts(products, targetId = 'productGrid', append = false) {
    const grid = document.getElementById(targetId);
    if (!grid) return;
    
    if (!append && products.length === 0) {
        grid.innerHTML = '<div class="empty-state">No products found.</div>';
        return;
    }
    const html = products.map(p => {
        const shortDescription = (p.description && p.description.length > 60)
            ? p.description.substring(0, 60) + "..."
            : (p.description || '');

        return `
            <div class="product-card">
                <button class="wishlist-btn ${wishlistIds.has(p.productId) ? 'active' : ''}" onclick="toggleWishlist('${p.productId}', this)">
                    <i class="fa-solid fa-heart"></i>
                </button>
                
                <div class="product-img-container">
                    <img src="${p.imageUrl || PLACEHOLDER}" 
                         onerror="this.onerror=null;this.src='${PLACEHOLDER}'"
                         class="product-img" alt="${p.name}">
                </div>

                <div class="product-name">${p.name}</div>
                <div class="product-desc" style="font-size: 0.85rem; color: #64748b; margin-bottom: 0.75rem; height: 2.4rem; overflow: hidden;">${shortDescription}</div>
                
                <div class="rating-stars">
                    ${generateStars(p.rating)}
                    <span class="rating-value">${p.rating || 0}</span>
                </div>

                <div class="price-section" style="flex-direction: column; align-items: flex-start; gap: 2px; margin-bottom: 1rem;">
                    ${p.discount > 0 ? `
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 2px;">
                            <span class="original-price" style="font-size: 0.9rem;">₹${p.price}</span>
                            <span class="discount-tag" style="font-size: 0.8rem; padding: 1px 6px;">${p.discount}% OFF</span>
                        </div>
                    ` : ''}
                    <div class="selling-price" style="font-size: 1.5rem; line-height: 1.2;">₹${p.sellingPrice || p.price}</div>
                </div>

                <div class="stock-status" style="margin-bottom: 1.25rem;">
                    ${p.stock > 10 ? `
                        <i class="fa-solid fa-circle-check status-in"></i>
                        <span class="status-in">In Stock</span>
                    ` : (p.stock > 0 ? `
                        <i class="fa-solid fa-triangle-exclamation" style="color: #f59e0b;"></i>
                        <span style="color: #f59e0b;">Low Stock (${p.stock} left)</span>
                    ` : `
                        <i class="fa-solid fa-circle-xmark status-out"></i>
                        <span class="status-out">Out of Stock</span>
                    `)}
                </div>

                <div class="card-actions">
                    <button class="btn btn-outline btn-sm" onclick="addToCart('${p.productId}')">
                        <i class="fa-solid fa-cart-plus"></i> Cart
                    </button>
                    <button class="btn btn-primary btn-sm btn-order" onclick="orderNow('${p.productId}')">
                        Order Now
                    </button>
                </div>
            </div>
        `;
    }).join('');

    if (append) {
        grid.insertAdjacentHTML('beforeend', html);
    } else {
        grid.innerHTML = html;
    }
}

function orderNow(pid) {
    const product = allProducts.find(p => p.productId === pid);
    if (!product) return;

    // Save selected product for checkout
    localStorage.setItem('checkoutProduct', JSON.stringify(product));
    
    // Redirect to checkout page
    window.location.href = 'checkout.html';
}

// (Old search logic removed; unified within loadProducts and DOMContentLoaded listener)

// 🛒 Cart Logic
async function addToCart(productId) {
    try {
        await apiCall('cart', 'POST', { productId, quantity: 1 });
        alert("Added to cart! 🛒");
    } catch (err) {
        alert("Error: " + err.message);
    }
}

async function loadCart() {
    try {
        const container = document.getElementById('cartItems');
        container.innerHTML = '<p>Loading your cart...</p>';
        const data = await apiCall('cart');
        const items = data.cart || [];

        if (items.length === 0) {
            container.innerHTML = '<div class="empty-state">Your cart is empty.</div>';
            return;
        }

        let total = 0;
        const html = items.map(item => {
            const price = item.sellingPrice || item.price || 0;
            const itemTotal = price * (item.quantity || 1);
            total += itemTotal;

            const shortDesc = (item.description && item.description.length > 50)
                ? item.description.substring(0, 50) + "..."
                : (item.description || '');

            return `
                <div class="list-item" style="display:flex; align-items:center; gap:1.5rem; background:white; padding:1.5rem; border-radius:12px; border:1px solid #f1f5f9; margin-bottom:1.5rem;">
                    <img src="${item.imageUrl || PLACEHOLDER}" 
                         onerror="this.onerror=null;this.src='${PLACEHOLDER}'"
                         style="width:80px; height:80px; object-fit:contain; background:#f8fafc; border-radius:12px; border:1px solid #f1f5f9;">
                    
                    <div style="flex:1;">
                        <h3 style="margin:0 0 5px; font-size:1.15rem; color:#1e293b;">${item.name}</h3>
                        <div style="font-size:0.85rem; color:#64748b; margin-bottom:10px;">${item.description || ''}</div>
                        
                        <button class="btn btn-outline btn-sm" style="color: #ef4444; border-color: #fecaca; padding: 4px 12px; font-size: 0.8rem; margin-top: 5px;" onclick="removeCart('${item.productId}')">
                            <i class="fa-solid fa-trash"></i> Remove
                        </button>
                    </div>

                    <div style="text-align:right;">
                        <div class="price-section" style="flex-direction: column; align-items: flex-end; gap: 2px; margin:0;">
                            ${item.discount > 0 ? `
                                <div style="display: flex; align-items: center; gap: 6px;">
                                    <span class="original-price" style="font-size: 0.85rem;">₹${item.price}</span>
                                    <span class="discount-tag" style="font-size: 0.75rem; padding: 1px 6px;">${item.discount}% OFF</span>
                                </div>
                            ` : ''}
                            <div class="selling-price" style="font-size: 1.3rem;">₹${price}</div>
                            <div style="font-size:0.8rem; color:#94a3b8; margin-top:4px;">Qty: ${item.quantity || 1}</div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = `
            ${html}
            <div style="margin-top:2rem; padding:1.5rem; background:#f8fafc; border-radius:12px; text-align:right;">
                <h3 style="margin:0; color:#64748b; font-size:1rem;">Cart Total</h3>
                <h2 style="margin:5px 0 1.5rem; color:#1e293b; font-size:1.75rem;">₹${total}</h2>
                <button class="btn btn-primary" style="width:200px;" onclick="checkoutCart()">
                    Checkout Now
                </button>
            </div>
        `;

        // Store items for checkout
        localStorage.setItem('checkoutItems', JSON.stringify(items));
    } catch (err) {
        console.error("Load Cart Error:", err);
    }
}

async function removeCart(productId) {
    if (!confirm("Remove this item from your cart?")) return;
    try {
        await apiCall('cart', 'DELETE', { productId });
        loadCart();
    } catch (err) {
        alert("Error: " + err.message);
    }
}

function checkoutCart() {
    const items = JSON.parse(localStorage.getItem('checkoutItems'));
    if (!items || items.length === 0) return;

    // Use a flag to tell checkout page we are doing multiple items
    localStorage.setItem('checkoutSource', 'cart');
    window.location.href = 'checkout.html';
}

// ❤️ Wishlist Logic
async function toggleWishlist(productId, btn) {
    console.log("Toggling Wishlist for Product ID:", productId);
    try {
        const res = await apiCall('wishlist', 'POST', { productId });
        console.log("Wishlist API Response:", res);
        
        if (res.wishlisted) {
            wishlistIds.add(productId);
            if (btn) btn.classList.add('active');
        } else {
            wishlistIds.delete(productId);
            if (btn) btn.classList.remove('active');
            
            // If we are in wishlist tab, refresh grid
            const currentTab = document.querySelector('.tab-content.active').id;
            if (currentTab === 'tab-wishlist') loadWishlist();
        }
    } catch (err) {
        alert("Error: " + err.message);
    }
}

async function loadWishlist() {
    try {
        const grid = document.getElementById('wishlistGrid');
        grid.innerHTML = '<p>Loading wishlist...</p>';
        const data = await apiCall('wishlist');
        renderProducts(data.products || [], 'wishlistGrid');
    } catch (err) {
        console.error("Load Wishlist Error:", err);
    }
}

// 📦 Orders Logic
async function loadOrders() {
    try {
        const container = document.getElementById('orderHistory');
        container.innerHTML = '<p>Loading orders...</p>';
        const data = await apiCall('orders');
        const orders = data.orders || [];

        if (orders.length === 0) {
            container.innerHTML = '<div class="empty-state">You haven\'t placed any orders yet.</div>';
            return;
        }

        container.innerHTML = orders.map(order => `
            <div class="list-item" style="background:white; padding:1.5rem; border-radius:12px; border:1px solid #f1f5f9; margin-bottom:1.5rem;">
                <div style="display:flex; justify-content:space-between; margin-bottom:1rem; padding-bottom:1rem; border-bottom:1px solid #f1f5f9;">
                    <div>
                        <span style="color:#64748b; font-size:0.9rem;">Order ID:</span>
                        <span style="font-weight:700; color:#1e293b; margin-left:5px;">#${order.orderId.slice(-8).toUpperCase()}</span>
                    </div>
                    <span class="status-badge" style="background:#f0fdf4; color:#16a34a; padding:4px 12px; border-radius:20px; font-weight:600; font-size:0.85rem;">
                        ${order.status || 'Processing'}
                    </span>
                </div>
                <div style="display:flex; gap:1.5rem; align-items:center;">
                    <img src="${order.imageUrl || PLACEHOLDER}" 
                         onerror="this.onerror=null;this.src='${PLACEHOLDER}'"
                         style="width:60px; height:60px; object-fit:contain;">
                    <div style="flex:1;">
                        <h4 style="margin:0; font-size:1.05rem;">${order.productName}</h4>
                        <p style="margin:5px 0; color:#64748b; font-size:0.9rem;">Ordered on: ${new Date(order.createdAt).toLocaleDateString()}</p>
                        <div style="display:flex; gap:15px; margin-top:8px; font-size:0.85rem; color:#64748b;">
                            <span>Qty: <strong style="color:#1e293b;">${order.quantity}</strong></span>
                            <span>Price: <strong style="color:#1e293b;">₹${order.price}</strong></span>
                        </div>
                    </div>
                    <div style="text-align:right;">
                        ${order.discount > 0 ? `
                            <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 2px; margin-bottom: 4px;">
                                <span style="text-decoration: line-through; color: #94a3b8; font-size: 0.85rem;">₹${order.originalPrice || ''}</span>
                                <span style="background: #f0fdf4; color: #16a34a; font-size: 0.75rem; padding: 1px 6px; border-radius: 4px; font-weight: 700;">${order.discount}% OFF</span>
                            </div>
                        ` : ''}
                        <p style="margin:0; font-weight:800; font-size:1.1rem; color:#0f172a;">₹${order.totalAmount}</p>
                        ${order.reviewed ? `
                            <div style="margin-top: 10px; background: #f0fdf4; color: #16a34a; padding: 6px 12px; border-radius: 8px; font-weight: 700; font-size: 0.85rem; display: inline-flex; align-items: center; gap: 5px;">
                                <i class="fa-solid fa-circle-check"></i> Reviewed
                            </div>
                        ` : (order.status === 'Delivered' ? `
                            <button class="btn btn-outline btn-sm" style="margin-top: 10px; border-color: #fbbf24; color: #d97706;" 
                                    onclick="openReviewPage('${order.productId}', '${order.orderId}')">
                                ⭐ Rate & Review
                            </button>
                        ` : '')}
                    </div>
                </div>
            </div>
        `).join('');
    } catch (err) {
        console.error("Load Orders Error:", err);
    }
}

function openReviewPage(productId, orderId) {
    window.location.href = `review.html?productId=${productId}&orderId=${orderId}`;
}

// 👤 Profile Logic
async function loadProfile() {
    try {
        const data = await apiCall('profile');
        Object.assign(user, data.profile);
        updateProfileUI();
    } catch (err) {
        console.error("Load Profile Error:", err);
    }
}


// 📑 Tab Management
function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
    document.getElementById(`tab-${tabId}`).classList.add('active');

    document.querySelectorAll('.sidebar-link').forEach(link => link.classList.remove('active'));
    const activeLink = document.querySelector(`.sidebar-link[data-target="${tabId}"]`);
    if (activeLink) activeLink.classList.add('active');

    // Toggle Search Bar visibility (Only show on dashboard)
    const searchBar = document.getElementById('searchBarContainer');
    if (searchBar) {
        searchBar.style.display = (tabId === 'dashboard') ? 'block' : 'none';
    }

    // Data Loaders
    if (tabId === 'dashboard') loadProducts();
    if (tabId === 'cart') loadCart();
    if (tabId === 'wishlist') loadWishlist();
    if (tabId === 'orders') loadOrders();
    if (tabId === 'profile') loadProfile();
}

function logout() {
    if (confirm("Are you sure you want to logout?")) {
        clearAuth();
        window.location.href = '../auth/login.html';
    }
}
