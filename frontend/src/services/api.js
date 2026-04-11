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

export const vehicleAPI = {
    getAll: (params) => api.get('/vehicles/', { params }),
    getById: (id) => api.get(`/vehicles/${id}`),
    getBrands: () => api.get('/vehicles/meta/brands'),
    compare: (ids) => api.post('/compare/', { ids }),
    recommend: (data) => api.post('/recommend/', data),
    getSubsidies: (params) => api.get('/subsidies/', { params }),
    getSubsidyPolicy: () => api.get('/subsidies/policy'),
    getMapStations: (params) => api.get('/map/stations', { params }),
};

export const chatAPI = {
  send: (payload) => chatApi.post('/chat/', payload),
  sendStream: async (payload, handlers = {}) => {
    const response = await fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
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
        } catch (_) {
          // Ignore malformed chunks.
        }
      }
    }
  },
};
