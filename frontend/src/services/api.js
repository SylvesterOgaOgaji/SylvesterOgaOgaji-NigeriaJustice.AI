/**
 * API Service for NigeriaJustice.AI
 * 
 * This module provides a configured axios instance for making API requests
 * with authentication, error handling, and request/response interceptors.
 */

import axios from 'axios';
import { getAuthToken, refreshAuthToken } from './auth';

// Get the base URL from environment or use default
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

// Request interceptor for adding auth token and handling requests
api.interceptors.request.use(
  async (config) => {
    // Get the auth token
    const token = await getAuthToken();
    
    // If token exists, add to headers
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for handling common errors and token refresh
api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    
    // Handle token expiration (401 Unauthorized)
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Attempt to refresh the token
        const newToken = await refreshAuthToken();
        
        // If successful, update the header and retry
        if (newToken) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        console.error('Token refresh failed:', refreshError);
        
        // Redirect to login if refresh fails
        window.location.href = '/login?session_expired=true';
        return Promise.reject(refreshError);
      }
    }
    
    // Handle server errors (500+)
    if (error.response?.status >= 500) {
      console.error('Server error:', error.response?.data || error.message);
      // You could add custom error handling or analytics here
    }
    
    // Handle other HTTP errors
    if (error.response) {
      console.error(`HTTP Error ${error.response.status}:`, error.response.data);
    } else if (error.request) {
      // Request was made but no response received
      console.error('No response received:', error.request);
    } else {
      // Error in setting up the request
      console.error('Request setup error:', error.message);
    }
    
    return Promise.reject(error);
  }
);

// Custom API methods for specific endpoints
const apiService = {
  // Authentication
  login: async (credentials) => {
    return api.post('/auth/login', credentials);
  },
  
  logout: async () => {
    return api.post('/auth/logout');
  },
  
  // Transcription
  startTranscriptionSession: async (sessionData) => {
    return api.post('/transcription/session/start', sessionData);
  },
  
  stopTranscriptionSession: async (sessionId) => {
    return api.post(`/transcription/session/${sessionId}/stop`);
  },
  
  transcribeAudio: async (formData) => {
    return api.post('/transcription/real-time', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },
  
  getTranscriptionJobs: async () => {
    return api.get('/transcription/jobs');
  },
  
  getTranscriptionJobStatus: async (jobId) => {
    return api.get(`/transcription/job/${jobId}`);
  },
  
  // Identity Verification
  verifyIdentity: async (identityData) => {
    return api.post('/identity/verify', identityData);
  },
  
  verifyCourtOfficial: async (officialData) => {
    return api.post('/identity/verify-official', officialData);
  },
  
  // Case Management
  getCases: async (params) => {
    return api.get('/cases', { params });
  },
  
  getCase: async (caseId) => {
    return api.get(`/cases/${caseId}`);
  },
  
  createCase: async (caseData) => {
    return api.post('/cases', caseData);
  },
  
  updateCase: async (caseId, caseData) => {
    return api.put(`/cases/${caseId}`, caseData);
  },
  
  uploadCaseDocument: async (caseId, formData) => {
    return api.post(`/cases/${caseId}/documents`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },
  
  // Warrant Transfer
  createWarrant: async (warrantData) => {
    return api.post('/warrants', warrantData);
  },
  
  transferWarrant: async (warrantId, transferData) => {
    return api.post(`/warrants/${warrantId}/transfer`, transferData);
  },
  
  getWarrantStatus: async (warrantId) => {
    return api.get(`/warrants/${warrantId}/status`);
  },
  
  // Virtual Court
  createVirtualSession: async (sessionData) => {
    return api.post('/virtual-court/sessions', sessionData);
  },
  
  joinVirtualSession: async (sessionId, participantData) => {
    return api.post(`/virtual-court/sessions/${sessionId}/join`, participantData);
  },
  
  // Judicial Support
  getDecisionSupport: async (caseId) => {
    return api.get(`/judicial/decision-support/${caseId}`);
  },
  
  searchLegalPrecedents: async (params) => {
    return api.get('/judicial/precedents', { params });
  },
  
  // System
  getSystemStatus: async () => {
    return api.get('/health');
  },
  
  // Generic request method for custom endpoints
  request: async (method, url, data = null, config = {}) => {
    return api({
      method,
      url,
      data,
      ...config
    });
  }
};

// Export both the configured axios instance and the API service
export { api };
export default apiService;
