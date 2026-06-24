// frontend/cliente-auth.js
(function () {
    const SESSION_KEY_STORAGE = 'cafeSessionKey';
    const AUTH_STORAGE = 'clienteAuth';   // base64("username:password")
    const INFO_STORAGE = 'clienteInfo';   // JSON {nombre, email, username}

    function uuidv4() {
        if (crypto.randomUUID) return crypto.randomUUID();
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    // La clave de sesión NO expira por sí misma: el backend limita la
    // visibilidad de pedidos de invitado a los creados en las últimas 12h.
    function getSessionKey() {
        let key = localStorage.getItem(SESSION_KEY_STORAGE);
        if (!key) {
            key = uuidv4();
            localStorage.setItem(SESSION_KEY_STORAGE, key);
        }
        return key;
    }

    function isClienteLoggedIn() {
        return !!localStorage.getItem(AUTH_STORAGE);
    }

    function getClienteInfo() {
        try { return JSON.parse(localStorage.getItem(INFO_STORAGE) || 'null'); }
        catch (e) { return null; }
    }

    function setClienteSession(username, password, clienteData) {
        localStorage.setItem(AUTH_STORAGE, btoa(`${username}:${password}`));
        localStorage.setItem(INFO_STORAGE, JSON.stringify(clienteData || {}));
    }

    function logoutCliente() {
        localStorage.removeItem(AUTH_STORAGE);
        localStorage.removeItem(INFO_STORAGE);
    }

    async function apiFetchCliente(url, options = {}) {
        const headers = Object.assign({}, options.headers || {});
        headers['X-Session-Key'] = getSessionKey();
        const auth = localStorage.getItem(AUTH_STORAGE);
        if (auth) headers['Authorization'] = `Basic ${auth}`;
        const res = await fetch(url, Object.assign({}, options, { headers }));
        if (res.status === 401) logoutCliente();
        return res;
    }

    window.CafeAuth = {
        getSessionKey, isClienteLoggedIn, getClienteInfo,
        setClienteSession, logoutCliente, apiFetchCliente
    };
})();