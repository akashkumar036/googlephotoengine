import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { getSession } from "next-auth/react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000,
});

// Attach JWT access token (automatically authenticates if not yet stored)
api.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    if (typeof window !== "undefined") {
      let token = localStorage.getItem("access_token");
      if (!token) {
        try {
          // Transparent auto-sign-in with default researcher credentials
          const res = await axios.post(`${API_BASE_URL}/auth/login`, {
            email: "admin@example.com",
            password: "change-me-admin-password",
          });
          if (res.data?.access_token) {
            token = res.data.access_token as string;
            localStorage.setItem("access_token", token);
            if (res.data.refresh_token) {
              localStorage.setItem("refresh_token", res.data.refresh_token as string);
            }
          }
        } catch {
          // If auto-login fails, try getSession fallback
          try {
            const session = await getSession();
            if (session?.user && (session.user as unknown as { accessToken?: string }).accessToken) {
              token = (session.user as unknown as { accessToken?: string }).accessToken as string;
              localStorage.setItem("access_token", token);
            }
          } catch {
            // Ignore
          }
        }
      }
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to transparently re-authenticate on 401
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    
    if (error.response?.status === 401 && !originalRequest._retry && typeof window !== "undefined") {
      originalRequest._retry = true;
      try {
        const res = await axios.post(`${API_BASE_URL}/auth/login`, {
          email: "admin@example.com",
          password: "change-me-admin-password",
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
      } catch (loginErr) {
        console.warn("Silent re-authentication failed", loginErr);
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

  // Stats (Overview)
  getStats: async () => {
    const res = await api.get("/stats");
    return res.data;
  },

  // Problems
  getProblems: async (params?: Record<string, any>) => {
    const res = await api.get("/problems", { params });
    return res.data;
  },
  getProblem: async (id: string) => {
    const res = await api.get(`/problems/${id}`);
    return res.data;
  },
  getProblemCrossPlatform: async (id: string) => {
    const res = await api.get(`/problems/${id}/cross-platform`);
    return res.data;
  },

  // Clusters
  getClusters: async () => {
    const res = await api.get("/clusters");
    return res.data;
  },
  getCluster: async (id: string) => {
    const res = await api.get(`/clusters/${id}`);
    return res.data;
  },

  // Trends
  getTrends: async (params?: { period?: string; granularity?: string }) => {
    const res = await api.get("/trends", { params });
    return res.data;
  },
  getEmergingTrends: async () => {
    const res = await api.get("/trends/emerging");
    return res.data;
  },

  // Conversations
  getConversations: async (params?: Record<string, any>) => {
    const res = await api.get("/conversations", { params });
    return res.data;
  },
  searchConversations: async (q: string, limit = 20) => {
    const res = await api.get("/conversations/search", { params: { q, limit } });
    return res.data;
  },
  getConversation: async (id: string) => {
    const res = await api.get(`/conversations/${id}`);
    return res.data;
  },

  // AI Research Assistant (RAG)
  askResearchAssistant: async (query: string, history?: any[], limit = 8) => {
    const res = await api.post("/research/query", { query, history, limit });
    return res.data;
  },
  getResearchStarters: async () => {
    const res = await api.get("/research/starters");
    return res.data;
  },

  // Human Review & Curation
  getReviewQueue: async (params?: { skip?: number; limit?: number; min_confidence?: number }) => {
    const res = await api.get("/reviews/queue", { params });
    return res.data;
  },
  submitReview: async (reviewData: {
    conversation_id: string;
    action: string;
    intent?: string;
    memory_types?: string[];
    failure_modes?: string[];
    is_relevant?: boolean;
    notes?: string;
  }) => {
    const res = await api.post("/reviews", reviewData);
    return res.data;
  },
  getTaxonomyReview: async () => {
    const res = await api.get("/reviews/taxonomy");
    return res.data;
  },
  handleProposalAction: async (proposalId: string, action: "approve" | "reject", notes?: string) => {
    const res = await api.post(`/reviews/taxonomy/proposals/${proposalId}/action`, { action, notes });
    return res.data;
  },
  handleClusterAction: async (clusterId: string, action: string, data: Record<string, any>) => {
    const res = await api.post(`/reviews/clusters/${clusterId}/action`, { action, ...data });
    return res.data;
  },

  // Research Briefs / Reports
  generateResearchBrief: async (params?: { problem_ids?: string[]; source_filter?: string; time_period?: string }) => {
    const res = await api.post("/reports/brief", params || {});
    return res.data;
  },
  listReports: async () => {
    const res = await api.get("/reports");
    return res.data;
  },
  getReport: async (id: string) => {
    const res = await api.get(`/reports/${id}`);
    return res.data;
  },
  exportReportUrl: (id: string, format = "markdown") => {
    return `${API_BASE_URL}/reports/${id}/export?format=${format}`;
  },

  // Jobs
  getJobs: async (limit = 10) => {
    const res = await api.get("/jobs", { params: { limit } });
    return res.data;
  },

  // Evaluation & Feedback Learning Loop
  getEvaluationResults: async () => {
    const res = await api.get("/evaluation/results");
    return res.data;
  },
  getBenchmarks: async () => {
    const res = await api.get("/evaluation/benchmarks");
    return res.data;
  },
  getFeedbackLoopInsights: async () => {
    const res = await api.get("/evaluation/feedback-loop");
    return res.data;
  },

  // Admin & Observability
  getAdminMetrics: async () => {
    const res = await api.get("/admin/metrics");
    return res.data;
  },
};
