// Auth Storage Helpers
function setAuth(token, user) {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
}

function getAuth() {
    const token = localStorage.getItem('token');
    const userStr = localStorage.getItem('user');
    return {
        token,
        user: userStr ? JSON.parse(userStr) : null
    };
}

function clearAuth() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
}

async function register(name, email, password, role = 'user') {
    const registerBtn = document.getElementById("registerBtn") || document.querySelector(".auth-submit-btn");
    if (registerBtn) {
        registerBtn.disabled = true;
        registerBtn.innerText = "Loading...";
    }
    try {
        const result = await apiCall('register', 'POST', {
            name,
            email,
            password,
            role
        });

        alert('Registration successful! Please login.');
        window.location.href = '/pages/auth/login.html';

    } catch (error) {
        alert(error.message);
        if (registerBtn) {
            registerBtn.disabled = false;
            registerBtn.innerText = "Register";
        }
    }
}

async function login(email, password) {
    const loginBtn = document.getElementById("loginBtn") || document.querySelector(".auth-submit-btn");
    if (loginBtn) {
        loginBtn.disabled = true;
        loginBtn.innerText = "Loading...";
    }
    try {
        const result = await apiCall('login', 'POST', {
            email,
            password
        });

        // Store token and user info in localStorage
        setAuth(result.token, result.user);
        
        // Redirect based on role
        if (result.user.role === 'seller') {
            window.location.href = '/pages/seller/dashboard.html';
        } else {
            window.location.href = '/pages/user/dashboard.html';
        }

    } catch (error) {
        alert(error.message);
        if (loginBtn) {
            loginBtn.disabled = false;
            loginBtn.innerText = "Login";
        }
    }
}

function logout() {
    clearAuth();
    window.location.href = '/pages/auth/login.html';
}

function checkAuth() {
    const auth = getAuth();
    
    if (!auth.token || !auth.user) {
        window.location.href = '/pages/auth/login.html';
        return null;
    }

    return auth.user;
}

