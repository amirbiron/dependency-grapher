/**
 * File Details Panel
 * מציג פרטים על קובץ שנבחר
 */

import React from 'react';
import { File, Code, AlertCircle } from 'lucide-react';
import './FileDetails.css';

const FileDetails = ({ file, blastRadius, onClose }) => {
  if (!file) {
    return (
      <div className="file-details-empty">
        <File size={48} className="empty-icon" />
        <p className="text-secondary">Select a file to view details</p>
      </div>
    );
  }

  return (
    <div className="file-details">
      {/* Header */}
      <div className="file-details-header">
        <div className="flex items-center gap-sm">
          <File size={20} />
          <h3 className="file-details-title truncate">{file.label}</h3>
        </div>
        {onClose && (
          <button className="btn-close" onClick={onClose}>
            ×
          </button>
        )}
      </div>

      {/* Path */}
      <div className="file-detail-section">
        <div className="detail-label">Path</div>
        <div className="detail-value font-mono text-sm">{file.full_path}</div>
      </div>

      {/* Stats */}
      <div className="file-detail-section">
        <div className="detail-label">Statistics</div>
        <div className="stats-grid">
          <div className="stat-item">
            <Code size={16} className="stat-icon" />
            <div>
              <div className="stat-value">{file.lines || 0}</div>
              <div className="stat-label">Lines</div>
            </div>
          </div>
          <div className="stat-item">
            <AlertCircle size={16} className="stat-icon" />
            <div>
              <div className="stat-value">{file.complexity?.toFixed(1) || 0}</div>
              <div className="stat-label">Complexity</div>
            </div>
          </div>
        </div>
      </div>

      {/* Type */}
      <div className="file-detail-section">
        <div className="detail-label">Type</div>
        <span className={`badge badge-${getTypeBadgeColor(file.type)}`}>
          {file.type || 'module'}
        </span>
      </div>

      {/* Blast Radius */}
      {blastRadius && (
        <div className="file-detail-section">
          <div className="detail-label">Blast Radius</div>
          <div className="blast-radius-info">
            <div className="blast-stat">
              <div className="blast-stat-value">
                {blastRadius.total_affected || 0}
              </div>
              <div className="blast-stat-label">Files Affected</div>
            </div>
            <div className="blast-stat">
              <div className="blast-stat-value">
                {blastRadius.risk_score?.toFixed(1) || 0}
              </div>
              <div className="blast-stat-label">Risk Score</div>
            </div>
          </div>

          {blastRadius.risk_level && (
            <span className={`badge badge-${blastRadius.risk_level}`}>
              {blastRadius.risk_level} risk
            </span>
          )}
        </div>
      )}

      {/* Dependents */}
      {blastRadius && blastRadius.direct_dependents && blastRadius.direct_dependents.length > 0 && (
        <div className="file-detail-section">
          <div className="detail-label">
            Direct Dependents ({blastRadius.direct_dependents.length})
          </div>
          <div className="dependents-list">
            {blastRadius.direct_dependents.slice(0, 5).map((dep, idx) => (
              <div key={idx} className="dependent-item">
                {dep.split('/').pop()}
              </div>
            ))}
            {blastRadius.direct_dependents.length > 5 && (
              <div className="text-secondary text-sm">
                +{blastRadius.direct_dependents.length - 5} more
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const getTypeBadgeColor = (type) => {
  const colors = {
    module: 'low',
    package: 'medium',
    script: 'high',
  };
  return colors[type] || 'low';
};

export default FileDetails;
