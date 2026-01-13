/**
 * Custom hook for managing analysis lifecycle
 */

import { useState, useEffect, useCallback } from 'react';
import { startAnalysis, getAnalysis, pollAnalysis } from '../services/api';

export const useAnalysis = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [analysisId, setAnalysisId] = useState(null);
  const [status, setStatus] = useState(null);
  const [progress, setProgress] = useState(0);

  /**
   * Start a new analysis
   */
  const analyze = useCallback(async (repoUrl, branch = 'main') => {
    setLoading(true);
    setError(null);
    setProgress(0);

    try {
      // Start analysis
      const result = await startAnalysis(repoUrl, branch);
      setAnalysisId(result.analysis_id);

      // Poll for completion
      await pollAnalysis(
        result.analysis_id,
        (statusUpdate) => {
          setStatus(statusUpdate);
          setProgress(statusUpdate.progress || 0);
        },
        2000, // poll every 2 seconds
        150 // max 5 minutes
      );

      setLoading(false);
      return result.analysis_id;
    } catch (err) {
      console.error('Analysis error:', err);
      setError(err.message || 'Analysis failed');
      setLoading(false);
      throw err;
    }
  }, []);

  /**
   * Load existing analysis
   */
  const loadAnalysis = useCallback(async (id) => {
    setLoading(true);
    setError(null);

    try {
      const data = await getAnalysis(id);
      setAnalysisId(id);
      setStatus(data);
      setProgress(data.progress || 0);
      setLoading(false);
      return data;
    } catch (err) {
      console.error('Load error:', err);
      setError(err.message || 'Failed to load analysis');
      setLoading(false);
      throw err;
    }
  }, []);

  /**
   * Reset state
   */
  const reset = useCallback(() => {
    setLoading(false);
    setError(null);
    setAnalysisId(null);
    setStatus(null);
    setProgress(0);
  }, []);

  return {
    loading,
    error,
    analysisId,
    status,
    progress,
    analyze,
    loadAnalysis,
    reset,
  };
};

export default useAnalysis;
