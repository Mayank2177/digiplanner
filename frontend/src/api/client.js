// client.js — single source of truth for talking to the FastAPI backend.
//
// The backend (see backend/main.py) exposes everything under /api/v1/*,
// protected by a JWT bearer token issued at /api/v1/auth/login|signup.
// This module centralizes: base URL config, attaching the token, parsing
// errors consistently, and auto-logout on 401 (expired/invalid token).

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export function getToken() {
  return localStorage.getItem('token');
}

function setSession({ access_token, email, name }) {
  localStorage.setItem('token', access_token);
  localStorage.setItem('userEmail', email);
  if (name) localStorage.setItem('userName', name);
  localStorage.setItem('isLoggedIn', 'true');
}

export function clearSession() {
  localStorage.removeItem('token');
  localStorage.removeItem('userEmail');
  localStorage.removeItem('userName');
  localStorage.removeItem('isLoggedIn');
}

export function isLoggedIn() {
  return !!getToken();
}

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function request(path, { method = 'GET', body, isForm = false, auth = true } = {}) {
  const headers = {};
  if (!isForm) headers['Content-Type'] = 'application/json';

  if (auth) {
    const token = getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
  }

  let res;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: body ? (isForm ? body : JSON.stringify(body)) : undefined,
    });
  } catch (networkErr) {
    throw new ApiError(
      `Could not reach the server at ${API_BASE_URL}. Is the backend running?`,
      0
    );
  }

  if (res.status === 204) return null;

  let data = null;
  const text = await res.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!res.ok) {
    // Expired/invalid token -> force re-login
    if (res.status === 401 && auth) {
      clearSession();
      if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    const detail = (data && (data.detail || data.message)) || res.statusText || 'Request failed';
    throw new ApiError(typeof detail === 'string' ? detail : JSON.stringify(detail), res.status);
  }

  return data;
}

// ── Auth ────────────────────────────────────────────────────────────────
export async function signup({ email, password, name, company, phone }) {
  const data = await request('/api/v1/auth/signup', {
    method: 'POST',
    auth: false,
    body: { email, password, name, company, phone },
  });
  setSession(data);
  return data;
}

export async function login({ email, password }) {
  const data = await request('/api/v1/auth/login', {
    method: 'POST',
    auth: false,
    body: { email, password },
  });
  setSession(data);
  return data;
}

export function getMe() {
  return request('/api/v1/auth/me');
}

export function setBudget(budget) {
  return request('/api/v1/auth/budget', { method: 'PUT', body: { budget } });
}

// ── Receipts ────────────────────────────────────────────────────────────
export function getReceipts(filters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') params.append(k, v);
  });
  const qs = params.toString();
  return request(`/api/v1/receipts${qs ? `?${qs}` : ''}`);
}

export function getReceipt(billId) {
  return request(`/api/v1/receipts/${encodeURIComponent(billId)}`);
}

export function updateReceipt(billId, updates) {
  return request(`/api/v1/receipts/${encodeURIComponent(billId)}`, {
    method: 'PATCH',
    body: updates,
  });
}

export function deleteReceipt(billId) {
  return request(`/api/v1/receipts/${encodeURIComponent(billId)}`, { method: 'DELETE' });
}

export function uploadReceipt(file) {
  const formData = new FormData();
  formData.append('file', file);
  return request('/api/v1/receipts/upload', {
    method: 'POST',
    isForm: true,
    body: formData,
  });
}

// ── Budget / Analytics ─────────────────────────────────────────────────
export function getBudgetSummary() {
  return request('/api/v1/budget/summary');
}

export function getSpendByCategory() {
  return request('/api/v1/analytics/spend-by-category');
}

export function getSubscriptions() {
  return request('/api/v1/analytics/subscriptions');
}

// ── Chat ────────────────────────────────────────────────────────────────
export function sendChatMessage(message) {
  return request('/api/v1/chat', { method: 'POST', body: { message } });
}

// ── ERP ─────────────────────────────────────────────────────────────────
export function syncToErp(system = 'SAP') {
  return request(`/api/v1/erp/sync?system=${encodeURIComponent(system)}`, { method: 'POST' });
}

export { ApiError, API_BASE_URL };
