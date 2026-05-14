// Check Auth
const user = checkAuth();
if (!user) window.location.href = '../auth/login.html';

const params = new URLSearchParams(window.location.search);
const productId = params.get('productId');
const orderId = params.get('orderId');

if (!productId || !orderId) {
    alert("Invalid Review Request");
    window.location.href = 'dashboard.html';
}

async function submitReview() {
    const rating = document.getElementById('rating').value;
    const comment = document.getElementById('comment').value.trim();
    const btn = document.getElementById('submitBtn');

    if (!comment) {
        alert("Please write a short review.");
        return;
    }

    btn.disabled = true;
    btn.innerText = "Submitting...";

    try {
        const payload = {
            productId,
            orderId,
            rating: parseInt(rating),
            comment
        };

        await apiCall('reviews', 'POST', payload);

        alert("🎉 Thank you! Your review has been added.");
        window.location.href = 'dashboard.html';
    } catch (err) {
        alert("Error: " + err.message);
        btn.disabled = false;
        btn.innerText = "Submit My Review";
    }
}
