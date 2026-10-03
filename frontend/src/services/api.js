import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth
export const login = (username, password) =>
  api.post('/auth/login', { username, password });

export const getUsers = () => api.get('/auth/users');

// Payments
export const checkPayment = (data) => api.post('/payments/check', data);

// Transactions
export const getTransactions = (params) => api.get('/transactions', { params });
export const getTransaction = (id) => api.get(`/transactions/${id}`);
export const getAccountTransactions = (accountId, params) =>
  api.get(`/accounts/${accountId}/transactions`, { params });

// Dashboard
export const getDashboardStats = () => api.get('/dashboard/stats');

// Alerts
export const getAlerts = (params) => api.get('/alerts', { params });
export const getAlert = (id) => api.get(`/alerts/${id}`);
export const updateAlert = (id, status) =>
  api.patch(`/alerts/${id}`, null, { params: { status } });

// Investigations
export const createInvestigation = (data) => api.post('/investigations', data);
export const getInvestigations = (params) => api.get('/investigations', { params });
export const getInvestigation = (id) => api.get(`/investigations/${id}`);
export const updateInvestigation = (id, data) => api.patch(`/investigations/${id}`, data);
export const addInvestigationNote = (id, content) =>
  api.post(`/investigations/${id}/notes`, { content });

// Network
export const getTransactionNetwork = (txId, depth = 2) =>
  api.get(`/network/${txId}`, { params: { depth } });
export const getFullNetwork = (limit = 100) =>
  api.get('/network', { params: { limit } });

// ML
export const predict = (data) => api.post('/ml/predict', data);
export const getModelInfo = () => api.get('/ml/model-info');

// Reports
export const getReportSummary = () => api.get('/reports/summary');

// Health
export const healthCheck = () => api.get('/health');

export default api;
