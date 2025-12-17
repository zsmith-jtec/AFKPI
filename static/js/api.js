/**
 * FOS API Helper
 * Handles authentication and API calls
 */

const api = {
    // Token storage key
    TOKEN_KEY: 'fos_token',
    USER_KEY: 'fos_user',

    /**
     * Get stored JWT token
     */
    getToken() {
        return localStorage.getItem(this.TOKEN_KEY);
    },

    /**
     * Get stored user info
     */
    getUser() {
        const user = localStorage.getItem(this.USER_KEY);
        return user ? JSON.parse(user) : null;
    },

    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return !!this.getToken();
    },

    /**
     * Login with email and password
     */
    async login(email, password) {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Login failed');
        }

        const data = await response.json();
        localStorage.setItem(this.TOKEN_KEY, data.access_token);

        // Fetch and store user info
        const userInfo = await this.get('/api/auth/me');
        localStorage.setItem(this.USER_KEY, JSON.stringify(userInfo));

        return data;
    },

    /**
     * Logout - clear token and redirect
     */
    logout() {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.USER_KEY);
        window.location.href = '/login';
    },

    /**
     * Make authenticated GET request
     */
    async get(url) {
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${this.getToken()}`
            }
        });

        if (response.status === 401) {
            this.logout();
            throw new Error('Session expired');
        }

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        return response.json();
    },

    /**
     * Make authenticated POST request
     */
    async post(url, data) {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.getToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (response.status === 401) {
            this.logout();
            throw new Error('Session expired');
        }

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        return response.json();
    },

    // Data formatting helpers
    formatCurrency(value) {
        if (value === null || value === undefined) return '--';
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(value);
    },

    formatPercent(value) {
        if (value === null || value === undefined) return '--';
        return `${parseFloat(value).toFixed(1)}%`;
    },

    formatWeek(year, week) {
        return `${year}-W${week.toString().padStart(2, '0')}`;
    }
};
