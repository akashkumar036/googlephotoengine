import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 15000,
});

// Attach JWT access token if available
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("access_token");
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to attempt refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    
    if (error.response?.status === 401 && !originalRequest._retry && typeof window !== "undefined") {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem("refresh_token");
      
      if (refreshToken) {
        try {
          const res = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          const { access_token, refresh_token: newRefreshToken } = res.data;
          localStorage.setItem("access_token", access_token);
          if (newRefreshToken) {
            localStorage.setItem("refresh_token", newRefreshToken);
          }
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${access_token}`;
          }
          return api(originalRequest);
        } catch {
          // Token refresh failed - clear tokens
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
        }
      }
    }
    return Promise.reject(error);
  }
);

// High-level API Service Helpers
export const ApiService = {
  // Health
  checkHealth: async () => {
    const res = await api.get("/health");
    return res.data;
  },

  // Auth
  login: async (credentials: { email: string; password: string }) => {
    const res = await api.post("/auth/login", credentials);
    if (typeof window !== "undefined") {
      localStorage.setItem("access_token", res.data.access_token);
      localStorage.setItem("refresh_token", res.data.refresh_token);
    }
    return res.data;
  },
  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    }
  },
  getMe: async () => {
    const res = await api.get("/auth/me");
    return res.data;
  },

  // Resources
  getProblems: async () => {
    const res = await api.get("/problems");
    return res.data;
  },
  getConversations: async () => {
    const res = await api.get("/conversations");
    return res.data;
  },
  getTrends: async () => {
    const res = await api.get("/trends");
    return res.data;
  },
  getClusters: async () => {
    const res = await api.get("/clusters");
    return res.data;
  },
  getReviews: async () => {
    const res = await api.get("/reviews");
    return res.data;
  },
  getResearch: async () => {
    const res = await api.get("/research");
    return res.data;
  },
  getReports: async () => {
    const res = await api.get("/reports");
    return res.data;
  },
};

export default api;
