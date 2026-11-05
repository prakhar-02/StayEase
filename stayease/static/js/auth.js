document.addEventListener('DOMContentLoaded', () => {
  const loginForm = document.getElementById('login-form');
  const registerForm = document.getElementById('register-form');

  if (loginForm) {
    // Redirect if already logged in
    if (isLoggedIn()) window.location.href = '/';

    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      hideError('login-error');

      const username = document.getElementById('username').value.trim();
      const password = document.getElementById('password').value;

      const res = await fetch('/api/auth/login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      const data = await res.json();

      if (res.ok) {
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);
        localStorage.setItem('username', username);

        const next = getUrlParam('next') || '/';
        window.location.href = next;
      } else {
        showError('login-error', data.detail || 'Invalid username or password.');
      }
    });
  }

  if (registerForm) {
    if (isLoggedIn()) window.location.href = '/';

    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      hideError('register-error');
      hideError('register-success');

      const payload = {
        username: document.getElementById('reg-username').value.trim(),
        email: document.getElementById('reg-email').value.trim(),
        phone_number: document.getElementById('reg-phone').value.trim(),
        password: document.getElementById('reg-password').value,
        password2: document.getElementById('reg-password2').value,
      };

      const res = await fetch('/api/auth/register/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (res.ok) {
        showSuccess('register-success', 'Account created! Redirecting to login...');
        setTimeout(() => window.location.href = '/login/', 1500);
      } else {
        const errors = Object.values(data).flat().join(' ');
        showError('register-error', errors || 'Registration failed.');
      }
    });
  }
});
