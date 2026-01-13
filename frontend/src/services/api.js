/**
 * API Client for Dependency Grapher
 */

import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('[API] Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log(`[API] Response:`, response.status);
    return response;
  },
  (error) => {
    console.error('[API] Response error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// ============================================
// API Methods
// ============================================

/**
 * Health check
 */
export const checkHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};

/**
 * Start analysis
 */
export const startAnalysis = async (repoUrl, branch = 'main', skipStdlib = true) => {
  const response = await api.post('/api/analyze', {
    repo_url: repoUrl,
    branch,
    skip_stdlib: skipStdlib,
  });
  return response.data;
};

/**
 * Get analysis status
 */
export const getAnalysis = async (analysisId) => {
  const response = await api.get(`/api/analysis/${analysisId}`);
  return response.data;
};

/**
 * Get graph data
 */
export const getGraph = async (analysisId, format = 'cytoscape') => {
  const response = await api.get(`/api/analysis/${analysisId}/graph`, {
    params: { format },
  });
  return response.data;
};

/**
 * Get blast radius for a file
 */
export const getBlastRadius = async (analysisId, filePath) => {
  const response = await api.get(
    `/api/analysis/${analysisId}/blast-radius/${encodeURIComponent(filePath)}`
  );
  return response.data;
};

/**
 * Get top risk files
 */
export const getRiskFiles = async (analysisId, limit = 10) => {
  const response = await api.get(`/api/analysis/${analysisId}/risk-files`, {
    params: { limit },
  });
  return response.data;
};

/**
 * Get project metrics
 */
export const getMetrics = async (analysisId) => {
  const response = await api.get(`/api/analysis/${analysisId}/metrics`);
  return response.data;
};

/**
 * Get files list
 */
export const getFiles = async (analysisId, search = '', riskLevel = null) => {
  const response = await api.get(`/api/analysis/${analysisId}/files`, {
    params: { search, risk_level: riskLevel },
  });
  return response.data;
};

/**
 * Delete analysis
 */
export const deleteAnalysis = async (analysisId) => {
  const response = await api.delete(`/api/analysis/${analysisId}`);
  return response.data;
};

/**
 * List analyses
 */
export const listAnalyses = async (limit = 20, offset = 0, status = null) => {
  const response = await api.get('/api/analyses', {
    params: { limit, offset, status },
  });
  return response.data;
};

/**
 * Poll analysis until complete
 */
export const pollAnalysis = async (
  analysisId,
  onProgress = null,
  pollInterval = 2000,
  maxAttempts = 150
) => {
  let attempts = 0;

  while (attempts < maxAttempts) {
    const status = await getAnalysis(analysisId);

    if (onProgress) {
      onProgress(status);
    }

    if (status.status === 'complete') {
      return status;
    }

    if (status.status === 'error') {
      throw new Error(status.error || 'Analysis failed');
    }

    attempts++;
    await new Promise((resolve) => setTimeout(resolve, pollInterval));
  }

  throw new Error('Analysis timeout');
};

export default api;
