/**
 * Risk Dashboard Component
 * מציג את הקבצים המסוכנים ביותר
 */

import React from 'react';
import { AlertTriangle, TrendingUp } from 'lucide-react';
import './RiskDashboard.css';

const RiskDashboard = ({ riskFiles, onFileClick }) => {
  if (!riskFiles || riskFiles.length === 0) {
    return (
      <div className="risk-dashboard-empty">
        <AlertTriangle size={32} className="empty-icon" />
        <p className="text-secondary text-sm">No risk data available</p>
      </div>
    );
  }

  return (
    <div className="risk-dashboard">
      <div className="risk-dashboard-header">
        <div className="flex items-center gap-sm">
          <AlertTriangle size={18} />
          <h3 className="risk-dashboard-title">Top Risk Files</h3>
        </div>
      </div>

      <div className="risk-files-list">
        {riskFiles.map((file, index) => (
          <div
            key={index}
            className="risk-file-item"
            onClick={() => onFileClick && onFileClick(file)}
          >
            <div className="risk-file-rank">{index + 1}</div>
            
            <div className="risk-file-info">
              <div className="risk-file-name">{file.file_path}</div>
              <div className="risk-file-details">
                <span className="risk-file-stat">
                  <TrendingUp size={12} />
                  {file.blast_radius} affected
                </span>
                <span className={`badge badge-${file.risk_level}`}>
                  {file.risk_level}
                </span>
              </div>
            </div>
            
            <div className="risk-file-score">
              <div className="risk-score-value">{file.risk_score}</div>
              <div className="risk-score-label">risk</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RiskDashboard;
