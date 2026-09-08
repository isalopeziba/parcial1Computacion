document.getElementById('login-form').addEventListener('submit', async function (event) {
    event.preventDefault();
    const error = document.getElementById('login-error');
    error.classList.add('d-none');
    const response = await fetch('/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            username: document.getElementById('username').value,
            password: document.getElementById('password').value
        })
    });
    const data = await response.json();
    if (!response.ok) {
        error.textContent = data.message || 'No fue posible iniciar sesión';
        error.classList.remove('d-none');
        return;
    }
    window.location.href = data.redirect;
});
