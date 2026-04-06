import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

const api = axios.create({
    baseURL: API_BASE,
    timeout: 5000
});

export const vehicleAPI = {
    getAll: (params) => api.get('/vehicles/', { params }),
    getById: (id) => api.get(`/vehicles/${id}`),
    getBrands: () => api.get('/vehicles/meta/brands'),
    compare: (ids) => api.post('/compare/', { ids }),
    recommend: (data) => api.post('/recommend/', data),
};