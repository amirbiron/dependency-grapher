/**
 * Main App Component
 * הרכיב הראשי שמחבר את כל הרכיבים
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Network } from 'lucide-react';
import AnalysisForm from './components/AnalysisForm';
import ProgressBar from './components/ProgressBar';
import ProjectStats from './components/ProjectStats';
import RiskDashboard from './components/RiskDashboard';
import GraphViewer from './components/GraphViewer';
import FileDetails from './components/FileDetails';
import { useAnalysis } from './hooks/useAnalysis';
import { getGraph, getBlastRadius, getRiskFiles } from './services/api';
import './styles/App.css';

function App() {
  // Analysis state
  const { loading, error, analysisId, status, progress, analyze, reset } = useAnalysis();

  // Graph state
  const [graphData, setGraphData] = useState(null);
  const [riskFiles, setRiskFiles] = useState([]);
  
  // UI state
  const [selectedFile, setSelectedFile] = useState(null);
  const [blastRadius, setBlastRadius] = useState(null);
  const [highlightedNodes, setHighlightedNodes] = useState([]);
  const [activeTab, setActiveTab] = useState('risk'); // 'risk' or 'details'

  const loadGraphData = useCallback(
    async (id) => {
      try {
        const data = await getGraph(id);
        setGraphData(data);
      } catch (err) {
        console.error('Failed to load graph:', err);
      }
    },
    [setGraphData]
  );

  const loadRiskFiles = useCallback(
    async (id) => {
      try {
        const data = await getRiskFiles(id, 10);
        setRiskFiles(data.risk_files || []);
      } catch (err) {
        console.error('Failed to load risk files:', err);
      }
    },
    [setRiskFiles]
  );

  // Load graph when analysis completes
  useEffect(() => {
    if (status?.status === 'complete' && analysisId) {
      loadGraphData(analysisId);
      loadRiskFiles(analysisId);
    }
  }, [status?.status, analysisId, loadGraphData, loadRiskFiles]);

  const handleStartAnalysis = async (repoUrl, branch) => {
    try {
      // Reset state
      setGraphData(null);
      setRiskFiles([]);
      setSelectedFile(null);
      setBlastRadius(null);
      setHighlightedNodes([]);

      // Start analysis
      await analyze(repoUrl, branch);
    } catch (err) {
      console.error('Analysis failed:', err);
    }
  };

  const handleNodeClick = async (node) => {
    setSelectedFile(node);
    setActiveTab('details');

    // Load blast radius
    try {
      const blast = await getBlastRadius(analysisId, node.full_path);
      setBlastRadius(blast);

      // Highlight affected nodes
      const affected = [
        node.id,
        ...(blast.direct_dependents || []),
        ...(blast.indirect_dependents || []),
      ];
      setHighlightedNodes(affected);
    } catch (err) {
      console.error('Failed to load blast radius:', err);
      setBlastRadius(null);
    }
  };

  const handleRiskFileClick = async (file) => {
    // Create a file object for display even if not in graph
    const fileData = {
      id: file.file_path,
      label: file.file_path.split('/').pop(),
      full_path: file.file_path,
      risk_score: file.risk_score,
      risk_level: file.risk_level,
      blast_radius_count: file.blast_radius
    };
    
    // Find node in graph for additional data
    if (graphData && graphData.elements && graphData.elements.nodes) {
      const node = graphData.elements.nodes.find(
        (n) => n.data.full_path === file.file_path
      );
      if (node) {
        // Merge graph data with risk file data
        Object.assign(fileData, node.data);
      }
    }
    
    // Set as selected file and switch to details tab
    setSelectedFile(fileData);
    setActiveTab('details');
    
    // Try to load blast radius data
    if (analysisId) {
      try {
        const blast = await getBlastRadius(analysisId, file.file_path);
        setBlastRadius(blast);
        
        // Highlight affected nodes in graph
        const affected = [
          fileData.id,
          ...(blast.direct_dependents || []),
          ...(blast.indirect_dependents || []),
        ];
        setHighlightedNodes(affected);
      } catch (err) {
        console.error('Failed to load blast radius:', err);
        // Set basic blast radius from risk file data
        setBlastRadius({
          file_path: file.file_path,
          total_affected: file.blast_radius || 0,
          risk_score: file.risk_score,
          risk_level: file.risk_level,
          direct_dependents: [],
          indirect_dependents: []
        });
      }
    }
  };

  const handleReset = () => {
    reset();
    setGraphData(null);
    setRiskFiles([]);
    setSelectedFile(null);
    setBlastRadius(null);
    setHighlightedNodes([]);
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-title">
          <Network className="header-title-icon" />
          Dependency Grapher
        </div>
        
        {status?.status === 'complete' && (
          <button className="btn btn-secondary" onClick={handleReset}>
            New Analysis
          </button>
        )}
      </header>

      {/* Main Content */}
      <main className="main-content">
        {/* Sidebar */}
        <aside className="sidebar">
          {/* Analysis Form */}
          {!loading && !status && (
            <div className="sidebar-section">
              <div className="sidebar-section-title">Start Analysis</div>
              <AnalysisForm onSubmit={handleStartAnalysis} loading={loading} />
            </div>
          )}

          {/* Progress */}
          {loading && (
            <div className="sidebar-section">
              <div className="sidebar-section-title">Analyzing...</div>
              <ProgressBar
                progress={progress}
                message={status?.progress_message}
                status={status?.status}
              />
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="sidebar-section">
              <div className="error-message">
                <strong>Error:</strong> {error}
              </div>
            </div>
          )}

          {/* Stats */}
          {status?.status === 'complete' && status.summary && (
            <div className="sidebar-section">
              <div className="sidebar-section-title">Project Stats</div>
              <ProjectStats summary={status.summary} />
            </div>
          )}

          {/* Tabs */}
          {status?.status === 'complete' && (
            <div className="sidebar-tabs">
              <button
                className={`sidebar-tab ${activeTab === 'risk' ? 'active' : ''}`}
                onClick={() => setActiveTab('risk')}
              >
                Risk Files
              </button>
              <button
                className={`sidebar-tab ${activeTab === 'details' ? 'active' : ''}`}
                onClick={() => setActiveTab('details')}
              >
                Details
              </button>
            </div>
          )}

          {/* Scrollable Content */}
          <div className="sidebar-scrollable">
            {status?.status === 'complete' && (
              <>
                {activeTab === 'risk' && (
                  <RiskDashboard
                    riskFiles={riskFiles}
                    onFileClick={handleRiskFileClick}
                  />
                )}
                {activeTab === 'details' && (
                  <FileDetails
                    file={selectedFile}
                    blastRadius={blastRadius}
                  />
                )}
              </>
            )}
          </div>
        </aside>

        {/* Graph Viewer */}
        <div className="graph-section">
          {!graphData && !loading && (
            <div className="empty-state">
              <Network size={64} className="empty-state-icon" />
              <h2>Welcome to Dependency Grapher</h2>
              <p className="text-secondary">
                Enter a repository URL to start analyzing dependencies
              </p>
            </div>
          )}

          {loading && (
            <div className="loading-container">
              <div className="spinner" />
              <p className="text-secondary">Analyzing repository...</p>
            </div>
          )}

          {graphData && graphData.elements && graphData.elements.nodes && graphData.elements.nodes.length > 0 && (
            <GraphViewer
              graphData={graphData}
              onNodeClick={handleNodeClick}
              highlightedNodes={highlightedNodes}
            />
          )}
          
          {/* Show message if graph data exists but is empty */}
          {graphData && (!graphData.elements || !graphData.elements.nodes || graphData.elements.nodes.length === 0) && !loading && (
            <div className="empty-state">
              <Network size={64} className="empty-state-icon" />
              <h2>No Dependencies Found</h2>
              <p className="text-secondary">
                The repository was analyzed but no Python dependencies were detected.
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
