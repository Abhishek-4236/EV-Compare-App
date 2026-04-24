import { create } from 'zustand';
import { authAPI } from '../services/api';

const TOKEN_KEY = 'eviq_token';
const USER_KEY = 'eviq_user';

const useAuth = create((set, get) => ({
  user: null,
  token: null,
  loading: true,

  // Called once on app start — restore session from localStorage
  initialize: async () => {
    const token = localStorage.getItem(TOKEN_KEY);
    const userStr = localStorage.getItem(USER_KEY);
    if (!token) {
      set({ loading: false });
      return;
    }
    try {
      const user = userStr ? JSON.parse(userStr) : null;
      set({ token, user, loading: false });
      // Validate token with backend
      const res = await authAPI.getMe(token);
      if (res.data?.user) {
        set({ user: res.data.user });
        localStorage.setItem(USER_KEY, JSON.stringify(res.data.user));
      }
    } catch {
      // Token expired or invalid — clear it
      get().logout();
    }
  },

  login: (token, user) => {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    set({ token, user });
  },

  logout: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    set({ user: null, token: null });
  },
}));

export default useAuth;
