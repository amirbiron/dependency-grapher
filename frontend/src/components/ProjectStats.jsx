/**
 * Project Statistics Component
 * מציג סטטיסטיקות על הפרויקט
 */

import React from 'react';
import { FileCode, GitBranch, AlertCircle, Layers } from 'lucide-react';
import './ProjectStats.css';

const ProjectStats = ({ summary }) => {
  if (!summary) {
    return null;
  }

  const stats = [
    {
      icon: <FileCode size={20} />,
      label: 'Files',
      value: summary.total_files || 0,
      color: 'var(--accent-primary)',
    },
    {
      icon: <GitBranch size={20} />,
      label: 'Imports',
      value: summary.total_imports || 0,
      color: 'var(--success)',
    },
    {
      icon: <Layers size={20} />,
      label: 'Classes',
      value: summary.total_classes || 0,
      color: 'var(--warning)',
    },
    {
      icon: <AlertCircle size={20} />,
      label: 'Errors',
      value: summary.error_files || 0,
      color: 'var(--error)',
    },
  ];

  return (
    <div className="project-stats">
      {stats.map((stat, index) => (
        <div key={index} className="stat-card">
          <div className="stat-icon" style={{ color: stat.color }}>
            {stat.icon}
          </div>
          <div className="stat-content">
            <div className="stat-value">{stat.value}</div>
            <div className="stat-label">{stat.label}</div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ProjectStats;
