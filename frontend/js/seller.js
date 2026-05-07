// Base URL is defined in api.js as API_BASE_URL

// 🔐 Authentication Protection (Immediate)
if (!localStorage.getItem("token")) {
    window.location.href = "/pages/auth/login.html";
}

let currentProduct = null;
let allProducts = [];

function switchTab(tabId) {
    // Update active states for sidebar items
    document.querySelectorAll('.sidebar-item').forEach(el => {
        if(el.dataset.target === tabId) {
            el.classList.add('active');
        } else {
            el.classList.remove('active');
        }
    });

    // Show selected tab content
    document.querySelectorAll('.tab-content').forEach(el => {
        el.classList.remove('active');
    });
    
    const targetTab = document.getElementById('tab-' + tabId);
    if (targetTab) {
        targetTab.classList.add('active');
    }
}

// ===== HANDLE FORM SUBMIT =====
function handleSubmit() {
    if (currentProduct) {
        updateProduct();
    } else {
        addProduct();
    }
}

// ===== LOAD STATS =====
async function loadStats() {
    try {
        const data = await apiCall('seller-stats');
        document.getElementById("totalProducts").innerText = data.totalProducts || 0;
        document.getElementById("totalOrders").innerText = data.totalOrders || 0;
        document.getElementById("totalSales").innerText = `₹ ${data.totalSales || 0}`;
        document.getElementById("lowStock").innerText = data.lowStock || 0;
    } catch (err) {
        console.error("Failed to load stats:", err);
    }
}

// ===== ADD PRODUCT =====
async function addProduct() {
    const file = document.getElementById("image").files[0];
    if (!file) return alert("Please select an image");

    try {
        // STEP 1: Get presigned upload URL
        const uploadData = await apiCall('get-upload-url', 'GET', null, { contentType: file.type });
        const { uploadUrl, imageUrl } = uploadData;

        // STEP 2: Upload image directly to S3
        const uploadRes = await fetch(uploadUrl, {
            method: "PUT",
            headers: {
                "Content-Type": file.type
            },
            body: file
        });

        if (!uploadRes.ok) {
            const errorText = await uploadRes.text();
            throw new Error(`S3 Upload Failed: ${uploadRes.status} ${uploadRes.statusText} - ${errorText}`);
        }

        // STEP 3: Save product with the permanent image URL
        const body = {
            name: document.getElementById("pName").value.trim(),
            price: Number(document.getElementById("pPrice").value),
            discount: Number(document.getElementById("pDiscount").value),
            description: document.getElementById("pDescription").value.trim(),
            stock: Number(document.getElementById("pStock").value),
            total: Number(document.getElementById("pTotal").value),
            imageUrl: imageUrl // ⭐ Use the S3 URL
        };

        const res = await apiCall('add-product', 'POST', body);
        alert(res.message || "Product added successfully!");
        
        resetForm();
        loadProducts();
        loadStats();
    } catch (err) {
        alert("Error adding product: " + err.message);
        console.error(err);
    }
}

// ===== EDIT PRODUCT (FILL FORM) =====
function editProduct(id) {
    const p = allProducts.find(item => item.productId === id);
    if (!p) return;

    currentProduct = p;

    document.getElementById("pName").value = p.name;
    document.getElementById("pPrice").value = p.price;
    document.getElementById("pDiscount").value = p.discount || 0;
    document.getElementById("pDescription").value = p.description;
    document.getElementById("pStock").value = p.stock;
    document.getElementById("pTotal").value = p.total || p.stock;

    // Change button text
    const btn = document.getElementById("submitBtn");
    btn.innerHTML = '<i class="fa-solid fa-check"></i> Update Product';
    
    // Scroll to form
    document.getElementById("tab-products").scrollIntoView({ behavior: 'smooth' });
}

// ===== UPDATE PRODUCT =====
async function updateProduct() {
    if (!currentProduct) return;

    try {
        const file = document.getElementById("image").files[0];
        let imageUrl = currentProduct.imageUrl; // Default to old image

        // If new image selected, upload it
        if (file) {
            const uploadData = await apiCall('get-upload-url');
            await fetch(uploadData.uploadUrl, {
                method: "PUT",
                headers: { "Content-Type": file.type },
                body: file
            });
            imageUrl = uploadData.imageUrl;
        }

        const body = {
            productId: currentProduct.productId,
            name: document.getElementById("pName").value.trim(),
            price: Number(document.getElementById("pPrice").value),
            discount: Number(document.getElementById("pDiscount").value),
            description: document.getElementById("pDescription").value.trim(),
            stock: Number(document.getElementById("pStock").value),
            total: Number(document.getElementById("pTotal").value),
            imageUrl: imageUrl
        };

        const res = await apiCall('update-product', 'PUT', body);
        console.log("UPDATE RESPONSE:", res);
        alert(res.message || "Product updated successfully!");

        resetForm();
        loadProducts();
        loadStats();
    } catch (err) {
        alert("Error updating product: " + err.message);
        console.error(err);
    }
}

function resetForm() {
    currentProduct = null;
    document.getElementById("addProductForm").reset();
    const btn = document.getElementById("submitBtn");
    btn.innerHTML = '<i class="fa-solid fa-plus"></i> Add Product';
}

// ===== LOAD PRODUCTS =====
async function loadProducts() {
    try {
        const data = await apiCall('seller-products');
        const productTable = document.getElementById("productTable");
        let html = "";

        const items = data.products || data; 
        allProducts = Array.isArray(items) ? items : [];

        allProducts.forEach(p => {
            const selling = p.price - (p.price * (p.discount || 0) / 100);

            html += `
                <tr>
                    <td><div style="font-weight: 600;">${p.name}</div></td>
                    <td>₹ ${p.price}</td>
                    <td><span style="color: var(--secondary); font-weight: 600;">${p.discount}% OFF</span></td>
                    <td style="font-weight: 700; color: var(--secondary);">₹ ${selling.toFixed(0)}</td>
                    <td>${p.stock}</td>
                    <td>${p.total || p.stock}</td>
                    <td>
                        <span class="status-badge ${p.stock > 10 ? 'status-success' : (p.stock > 0 ? 'status-warning' : 'status-danger')}">
                            ${p.stock > 10 ? 'In Stock' : (p.stock > 0 ? 'Low Stock' : 'Out of Stock')}
                        </span>
                    </td>
                    <td>
                        <button class="btn btn-sm btn-primary" onclick="editProduct('${p.productId}')"><i class="fa-solid fa-pen-to-square"></i></button>
                        <button class="btn btn-sm btn-danger" onclick="deleteProduct('${p.productId}')"><i class="fa-solid fa-trash"></i></button>
                    </td>
                </tr>
            `;
        });

        productTable.innerHTML = html || '<tr><td colspan="8" style="text-align:center;">No products found</td></tr>';
    } catch (err) {
        console.error("Failed to load products:", err);
    }
}

// ===== DELETE PRODUCT =====
async function deleteProduct(id) {
    if (!confirm("Are you sure you want to delete this product?")) return;

    try {
        await apiCall('delete-product', 'DELETE', { productId: id });
        loadProducts();
        loadStats();
    } catch (err) {
        alert("Error deleting product: " + err.message);
    }
}

// ===== LOAD ORDERS =====
async function loadOrders() {
    try {
        const data = await apiCall('seller-orders');
        const ordersTable = document.getElementById("ordersTable");
        const recentOrders = document.getElementById("recentOrders");
        
        let html = "";
        let recentHtml = "";

        const items = data.orders || data;
        const ordersList = Array.isArray(items) ? items : [];

        ordersList.forEach((o, i) => {
            const row = `
                <tr>
                    <td><span style="font-weight: 600;">#${o.orderId.substring(0, 8)}</span></td>
                    <td>${o.productName || 'Product'}</td>
                    <td>${o.userName || 'Customer'}</td>
                    <td>${o.quantity}</td>
                    <td><span class="status-badge ${getStatusClass(o.status)}">${o.status}</span></td>
                    <td>${actionBtn(o)}</td>
                </tr>
            `;
            html += row;
            if (i < 5) recentHtml += row;
        });

        ordersTable.innerHTML = html || '<tr><td colspan="6" style="text-align:center;">No orders found</td></tr>';
        recentOrders.innerHTML = recentHtml || '<tr><td colspan="4" style="text-align:center;">No recent orders</td></tr>';
    } catch (err) {
        console.error("Failed to load orders:", err);
    }
}

function getStatusClass(status) {
    switch (status) {
        case 'Processing': return 'status-warning';
        case 'Shipped': return 'status-info';
        case 'Delivered': return 'status-success';
        default: return '';
    }
}

// ===== ACTION BUTTON =====
function actionBtn(o) {
    if (o.status === "Processing") {
        return `<button class="btn btn-sm btn-success" onclick="updateStatus('${o.orderId}','Shipped')"><i class="fa-solid fa-truck"></i> Mark Shipped</button>`;
    }
    if (o.status === "Shipped") {
        return `<button class="btn btn-sm btn-primary" onclick="updateStatus('${o.orderId}','Delivered')"><i class="fa-solid fa-check-double"></i> Mark Delivered</button>`;
    }
    return '<span style="color: var(--text-muted); font-size: 0.85rem; font-weight: 500;"><i class="fa-solid fa-check"></i> Completed</span>';
}

// ===== UPDATE STATUS =====
async function updateStatus(orderId, status) {
    try {
        await apiCall('update-order-status', 'PUT', { orderId, status });
        loadOrders();
        loadStats();
    } catch (err) {
        alert("Error updating status: " + err.message);
    }
}

// Check authentication on load
document.addEventListener('DOMContentLoaded', () => {
    const user = checkAuth();
    if (user && user.role === 'seller') {
        const welcomeHeader = document.querySelector('.welcome-header h1');
        if (welcomeHeader) {
            welcomeHeader.textContent = `Welcome back, ${user.name}!`;
        }
        init();
    } else if (user) {
        window.location.href = '../user/dashboard.html';
    }
});

// ===== INIT =====
function init() {
    loadStats();
    loadProducts();
    loadOrders();
}
