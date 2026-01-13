/**
 * Progress Bar Component
 * מציג התקדמות הניתוח
 */

import React from 'react';
import './ProgressBar.css';

const ProgressBar = ({ progress, message, status }) => {
  const getStatusColor = () => {
    switch (status) {
      case 'complete':
        return 'var(--success)';
      case 'error':
        return 'var(--error)';
      case 'processing':
        return 'var(--accent-primary)';
      default:
        return 'var(--text-tertiary)';
    }
  };

  return (
    <div className="progress-bar-container">
      <div className="progress-bar-header">
        <span className="progress-percentage">{progress}%</span>
        {message && <span className="progress-message">{message}</span>}
      </div>
      
      <div className="progress-bar-track">
        <div
          className="progress-bar-fill"
          style={{
            width: `${progress}%`,
            backgroundColor: getStatusColor(),
          }}
        />
      </div>
    </div>
  );
};

export default ProgressBar;
