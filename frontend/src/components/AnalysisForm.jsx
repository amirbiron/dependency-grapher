/**
 * Analysis Form Component
 * טופס להתחלת ניתוח חדש
 */

import React, { useState } from 'react';
import { Play, Github } from 'lucide-react';
import './AnalysisForm.css';

const AnalysisForm = ({ onSubmit, loading }) => {
  const [repoUrl, setRepoUrl] = useState('');
  const [branch, setBranch] = useState('main');
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Validation
    if (!repoUrl.trim()) {
      setError('Please enter a repository URL');
      return;
    }

    // Basic URL validation
    if (!repoUrl.includes('github.com') && !repoUrl.includes('gitlab.com')) {
      setError('Please enter a valid GitHub or GitLab URL');
      return;
    }

    setError('');
    onSubmit(repoUrl, branch);
  };

  return (
    <form className="analysis-form" onSubmit={handleSubmit}>
      <div className="form-group">
        <label htmlFor="repo-url" className="form-label">
          <Github size={16} />
          Repository URL
        </label>
        <input
          id="repo-url"
          type="text"
          className="input"
          placeholder="https://github.com/user/repo"
          value={repoUrl}
          onChange={(e) => setRepoUrl(e.target.value)}
          disabled={loading}
        />
      </div>

      <div className="form-group">
        <label htmlFor="branch" className="form-label">
          Branch
        </label>
        <input
          id="branch"
          type="text"
          className="input"
          placeholder="main"
          value={branch}
          onChange={(e) => setBranch(e.target.value)}
          disabled={loading}
        />
      </div>

      {error && (
        <div className="form-error">
          {error}
        </div>
      )}

      <button
        type="submit"
        className="btn btn-primary btn-full"
        disabled={loading}
      >
        {loading ? (
          <>
            <div className="spinner-sm" />
            Analyzing...
          </>
        ) : (
          <>
            <Play size={16} />
            Start Analysis
          </>
        )}
      </button>
    </form>
  );
};

export default AnalysisForm;
