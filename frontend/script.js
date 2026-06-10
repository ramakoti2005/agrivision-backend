document.addEventListener('DOMContentLoaded', () => {
    // --- API Base URL Detection ---
    // Using 127.0.0.1 is more reliable than 'localhost' on Windows systems
    const API_BASE = (window.location.port === '8000') ? '' : 'http://127.0.0.1:8000';

    console.log("AgriVision AI: Initializing connection to:", API_BASE || "Self (Port 8000)");

    // --- Elements ---
    const authSection = document.getElementById('auth-section');
    const tabLogin = document.getElementById('tab-login');
    const tabRegister = document.getElementById('tab-register');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const loginError = document.getElementById('login-error');
    const registerError = document.getElementById('register-error');
    const logoutBtn = document.getElementById('logout-btn');
    const appNav = document.getElementById('app-nav');
    const uploadSection = document.getElementById('upload-section');
    const resultsSection = document.getElementById('results-section');
    const loadingSection = document.getElementById('loading-section');
    const historySection = document.getElementById('history-section');
    const tabScanView = document.getElementById('tab-scan-view');
    const tabHistoryView = document.getElementById('tab-history-view');

    // Navigation Tabs
    const backToHistoryBtn = document.getElementById('back-to-history-btn');
    const newScanBtn = document.getElementById('new-scan-btn');

    let authToken = localStorage.getItem('token');
    let currentFile = null;

    // --- Startup Check ---
    if (authToken) {
        showApp();
    } else {
        showAuth();
    }

    // --- Password Toggle ---
    const setupToggle = (btnId, inputId) => {
        const btn = document.getElementById(btnId);
        const input = document.getElementById(inputId);
        if(btn && input) {
            btn.onclick = () => {
                const icon = btn.querySelector('i');
                input.type = input.type === 'password' ? 'text' : 'password';
                icon.classList.toggle('fa-eye');
                icon.classList.toggle('fa-eye-slash');
            };
        }
    };
    setupToggle('btn-toggle-login-pwd', 'login-password');
    setupToggle('btn-toggle-reg-pwd', 'reg-password');

    // --- Utility: Error Handler ---
    const handleConnectionError = (err, errorElement) => {
        console.error("API Connection Error:", err);
        let msg = err.message;
        if (msg === "Failed to fetch") {
            msg = "Backend Offline: Run 'uvicorn app.main:app --reload' in your terminal and refresh.";
        }
        errorElement.innerText = msg;
        errorElement.style.display = 'block';
    };

    // --- Auth Logic ---
    tabLogin.addEventListener('click', () => {
        tabLogin.classList.add('active'); tabRegister.classList.remove('active');
        loginForm.classList.remove('hidden'); registerForm.classList.add('hidden');
        loginError.style.display = 'none';
    });

    tabRegister.addEventListener('click', () => {
        tabRegister.classList.add('active'); tabLogin.classList.remove('active');
        registerForm.classList.remove('hidden'); loginForm.classList.add('hidden');
        registerError.style.display = 'none';
    });

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;
        loginError.style.display = 'none';

        try {
            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);

            const res = await fetch(`${API_BASE}/api/v1/auth/token`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData
            });

            if (!res.ok) {
                const data = await res.json().catch(() => ({ detail: "Invalid credentials" }));
                throw new Error(data.detail || "Login failed");
            }

            const data = await res.json();
            authToken = data.access_token;
            localStorage.setItem('token', authToken);
            showApp();
        } catch (err) {
            handleConnectionError(err, loginError);
        }
    });

    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('reg-username').value.trim();
        const email = document.getElementById('reg-email').value.trim();
        const password = document.getElementById('reg-password').value;
        registerError.style.display = 'none';

        try {
            const res = await fetch(`${API_BASE}/api/v1/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, email, password })
            });

            if (!res.ok) {
                const data = await res.json().catch(() => ({ detail: "Registration failed" }));
                let msg = data.detail;
                if (Array.isArray(msg)) msg = msg.map(m => m.msg).join(", ");
                throw new Error(msg || "Registration failed");
            }

            alert("Registration successful! Please login.");
            tabLogin.click();
            document.getElementById('login-username').value = username;
        } catch (err) {
            handleConnectionError(err, registerError);
        }
    });

    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('token');
        authToken = null;
        showAuth();
    });

    function showApp() {
        authSection.classList.add('hidden');
        appNav.classList.remove('hidden');
        tabScanView.click();
    }

    function showAuth() {
        authSection.classList.remove('hidden');
        appNav.classList.add('hidden');
        uploadSection.classList.add('hidden');
        resultsSection.classList.add('hidden');
        historySection.classList.add('hidden');
    }

    // --- Navigation ---
    tabScanView.onclick = () => {
        tabScanView.classList.add('active'); tabHistoryView.classList.remove('active');
        historySection.classList.add('hidden');
        if(resultsSection.classList.contains('hidden')) uploadSection.classList.remove('hidden');
    };

    tabHistoryView.onclick = () => {
        tabHistoryView.classList.add('active'); tabScanView.classList.remove('active');
        uploadSection.classList.add('hidden'); resultsSection.classList.add('hidden');
        historySection.classList.remove('hidden');
    };

    // --- File Handling ---
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const browseBtn = document.getElementById('browse-btn');

    browseBtn.onclick = () => fileInput.click();
    fileInput.onchange = (e) => handleFile(e.target.files[0]);

    function handleFile(file) {
        if (!file) return;
        currentFile = file;
        const reader = new FileReader();
        reader.onload = (e) => {
            document.getElementById('image-preview').src = e.target.result;
            dropZone.classList.add('hidden');
            document.getElementById('preview-container').classList.remove('hidden');
        };
        reader.readAsDataURL(file);
    }

    document.getElementById('clear-btn').onclick = () => {
        currentFile = null; fileInput.value = '';
        dropZone.classList.remove('hidden');
        document.getElementById('preview-container').classList.add('hidden');
    };

    document.getElementById('analyze-btn').onclick = async () => {
        if (!currentFile) return;
        uploadSection.classList.add('hidden');
        loadingSection.classList.remove('hidden');

        const formData = new FormData();
        formData.append('file', currentFile);

        try {
            const res = await fetch(`${API_BASE}/api/v1/analyze`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${authToken}` },
                body: formData
            });
            if (!res.ok) throw new Error("Analysis failed");
            const data = await res.json();
            displayResults(data);
        } catch (err) {
            alert(err.message);
            loadingSection.classList.add('hidden');
            uploadSection.classList.remove('hidden');
        }
    };

    newScanBtn.onclick = () => {
        resultsSection.classList.add('hidden');
        document.getElementById('clear-btn').click();
        uploadSection.classList.remove('hidden');
    };

    function displayResults(data) {
        document.getElementById('res-plant').innerText = data.plant_name;
        document.getElementById('res-scientific').innerText = data.scientific_name;
        document.getElementById('res-confidence').innerText = data.confidence;
        document.getElementById('res-quality').innerText = data.image_quality;
        document.getElementById('res-solution').innerText = data.solution_suggestion;

        loadingSection.classList.add('hidden');
        resultsSection.classList.remove('hidden');
    }
});
