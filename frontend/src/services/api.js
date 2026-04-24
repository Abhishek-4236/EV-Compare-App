import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : (import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000/api');

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 5000,
});

const chatApi = axios.create({
  baseURL: API_BASE,
  timeout: 20000,
});

// Attach JWT token to every request automatically
const attachToken = (config) => {
  const token = localStorage.getItem('eviq_token');
  if (token) config.headers['Authorization'] = `Bearer ${token}`;
  return config;
};
api.interceptors.request.use(attachToken);
chatApi.interceptors.request.use(attachToken);

export const vehicleAPI = {
    getAll: (params) => api.get('/vehicles/', { params }),
    getDiverseFeatured: () => api.get('/vehicles/featured/diverse'),
    getById: (id) => api.get(`/vehicles/${id}`),
    getBrands: () => api.get('/vehicles/meta/brands'),
    compare: (ids) => api.post('/compare/', { ids }),
    recommend: (data) => api.post('/recommend/', data),
    getSubsidies: (params) => api.get('/subsidies/', { params }),
    getSubsidyPolicy: () => api.get('/subsidies/policy'),
    getMapStations: (params) => api.get('/map/stations', { params }),
};

export const authAPI = {
  signup: (data) => api.post('/auth/signup', data),
  login: (data) => api.post('/auth/login', data),
  getMe: (token) => api.get('/auth/me', { headers: { Authorization: `Bearer ${token}` } }),
};

export const garageAPI = {
  get: () => api.get('/garage'),
  save: (data) => api.post('/garage', data),
  remove: (id) => api.delete(`/garage/${id}`),
};

export const adminAPI = {
  uploadDataset: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/admin/upload-dataset', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  getStats: () => api.get('/admin/stats'),
};

export const chatAPI = {
  send: (payload) => chatApi.post('/chat/', payload),
  getSessions: () => chatApi.get('/chat/sessions'),
  getHistory: (sessionId) => chatApi.get(`/chat/history/${sessionId}`),
  sendStream: async (payload, handlers = {}) => {
    const token = localStorage.getItem('eviq_token');
    const response = await fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(payload),
    });
    if (!response.ok || !response.body) throw new Error('SSE stream failed');

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split('\n\n');
      buffer = events.pop() || '';

      for (const event of events) {
        if (!event.startsWith('data: ')) continue;
        const payloadText = event.slice(6);
        try {
          const data = JSON.parse(payloadText);
          if (data.type === 'session' && handlers.onSession) handlers.onSession(data.session_id);
          if (data.type === 'chunk' && handlers.onChunk) handlers.onChunk(data.content);
          if (data.type === 'done' && handlers.onDone) handlers.onDone(data);
        } catch {
          // Ignore malformed chunks.
        }
      }
    }
  },
};

