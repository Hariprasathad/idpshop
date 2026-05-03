document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    try {
        await login(email, password);
    } catch (error) {
        console.error('Login failed:', error);
    }
});
