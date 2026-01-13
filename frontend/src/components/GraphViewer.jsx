/**
 * Graph Viewer Component
 * הרכיב המרכזי - מציג את הגרף עם Cytoscape.js
 */

import React, { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import coseBilkent from 'cytoscape-cose-bilkent';
import { ZoomIn, ZoomOut, Maximize2, Download } from 'lucide-react';
import './GraphViewer.css';

// Register layout
cytoscape.use(coseBilkent);

const GraphViewer = ({ graphData, onNodeClick, highlightedNodes = [] }) => {
  const containerRef = useRef(null);
  const cyRef = useRef(null);
  const [layout, setLayout] = useState('cose-bilkent');

  useEffect(() => {
    // Validate we have container and valid graph data
    if (!containerRef.current) {
      console.log('[GraphViewer] No container ref');
      return;
    }
    
    if (!graphData || !graphData.elements) {
      console.log('[GraphViewer] No graph data or elements');
      return;
    }
    
    const { nodes, edges } = graphData.elements;
    if (!nodes || nodes.length === 0) {
      console.log('[GraphViewer] No nodes in graph data');
      return;
    }
    
    console.log(`[GraphViewer] Initializing with ${nodes.length} nodes and ${edges?.length || 0} edges`);

    // Initialize Cytoscape
    const cy = cytoscape({
      container: containerRef.current,
      elements: graphData.elements,
      style: getGraphStyle(),
      layout: {
        name: layout,
        ...getLayoutConfig(layout),
      },
      minZoom: 0.1,
      maxZoom: 3,
      wheelSensitivity: 0.2,
    });

    cyRef.current = cy;

    // Event handlers
    cy.on('tap', 'node', (event) => {
      const node = event.target;
      if (onNodeClick) {
        onNodeClick(node.data());
      }
    });

    // Cleanup
    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
        cyRef.current = null;
      }
    };
  }, [graphData, layout, onNodeClick]);

  // Update highlights
  useEffect(() => {
    if (!cyRef.current) return;

    const cy = cyRef.current;

    // Reset all
    cy.nodes().removeClass('highlighted dimmed');
    cy.edges().removeClass('highlighted dimmed');

    if (highlightedNodes.length > 0) {
      // Highlight selected nodes
      const highlighted = cy.nodes().filter((node) =>
        highlightedNodes.includes(node.id())
      );

      highlighted.addClass('highlighted');

      // Dim others
      cy.nodes().not(highlighted).addClass('dimmed');
      cy.edges().addClass('dimmed');

      // Highlight connected edges
      highlighted.connectedEdges().removeClass('dimmed').addClass('highlighted');
    }
  }, [highlightedNodes]);

  // ============================================
  // Controls
  // ============================================

  const handleZoomIn = () => {
    if (cyRef.current) {
      cyRef.current.zoom(cyRef.current.zoom() * 1.2);
    }
  };

  const handleZoomOut = () => {
    if (cyRef.current) {
      cyRef.current.zoom(cyRef.current.zoom() * 0.8);
    }
  };

  const handleFit = () => {
    if (cyRef.current) {
      cyRef.current.fit(null, 50);
    }
  };

  const handleExportPNG = () => {
    if (cyRef.current) {
      const png = cyRef.current.png({ scale: 2 });
      const link = document.createElement('a');
      link.href = png;
      link.download = 'dependency-graph.png';
      link.click();
    }
  };

  const handleChangeLayout = (newLayout) => {
    setLayout(newLayout);
    if (cyRef.current) {
      cyRef.current.layout({
        name: newLayout,
        ...getLayoutConfig(newLayout),
      }).run();
    }
  };

  return (
    <div className="graph-viewer">
      <div ref={containerRef} className="graph-container" />

      {/* Controls */}
      <div className="graph-controls">
        <div className="control-group">
          <button
            className="control-btn"
            onClick={handleZoomIn}
            title="Zoom In"
          >
            <ZoomIn size={18} />
          </button>
          <button
            className="control-btn"
            onClick={handleZoomOut}
            title="Zoom Out"
          >
            <ZoomOut size={18} />
          </button>
          <button className="control-btn" onClick={handleFit} title="Fit">
            <Maximize2 size={18} />
          </button>
        </div>

        <div className="control-group">
          <button
            className="control-btn"
            onClick={handleExportPNG}
            title="Export PNG"
          >
            <Download size={18} />
          </button>
        </div>
      </div>

      {/* Layout Selector */}
      <div className="layout-selector">
        <select
          value={layout}
          onChange={(e) => handleChangeLayout(e.target.value)}
          className="layout-select"
        >
          <option value="cose-bilkent">Force Directed</option>
          <option value="circle">Circle</option>
          <option value="grid">Grid</option>
          <option value="breadthfirst">Hierarchy</option>
        </select>
      </div>
    </div>
  );
};

// ============================================
// Graph Style
// ============================================

const getGraphStyle = () => [
  {
    selector: 'node',
    style: {
      'background-color': '#4f93ff',
      'label': 'data(label)',
      'color': '#e8eaed',
      'text-valign': 'center',
      'text-halign': 'center',
      'font-size': '10px',
      'width': '30px',
      'height': '30px',
      'border-width': '2px',
      'border-color': '#1a1f2e',
    },
  },
  {
    selector: 'node[type="package"]',
    style: {
      'background-color': '#8ab4f8',
      'shape': 'rectangle',
    },
  },
  {
    selector: 'node[type="script"]',
    style: {
      'background-color': '#34a853',
      'shape': 'diamond',
    },
  },
  {
    selector: 'edge',
    style: {
      'width': 1,
      'line-color': '#5f6368',
      'target-arrow-color': '#5f6368',
      'target-arrow-shape': 'triangle',
      'curve-style': 'bezier',
      'arrow-scale': 0.8,
    },
  },
  {
    selector: 'edge[is_relative="true"]',
    style: {
      'line-style': 'dashed',
    },
  },
  {
    selector: '.highlighted',
    style: {
      'background-color': '#fbbc04',
      'line-color': '#fbbc04',
      'target-arrow-color': '#fbbc04',
      'width': 2,
      'z-index': 999,
    },
  },
  {
    selector: 'node.highlighted',
    style: {
      'border-width': '3px',
      'border-color': '#fbbc04',
      'font-weight': 'bold',
    },
  },
  {
    selector: '.dimmed',
    style: {
      'opacity': 0.2,
    },
  },
];

// ============================================
// Layout Configs
// ============================================

const getLayoutConfig = (layoutName) => {
  const configs = {
    'cose-bilkent': {
      animate: true,
      animationDuration: 500,
      nodeDimensionsIncludeLabels: true,
      idealEdgeLength: 100,
      nodeRepulsion: 4500,
      gravity: 0.1,
    },
    circle: {
      animate: true,
      animationDuration: 500,
      avoidOverlap: true,
      radius: 200,
    },
    grid: {
      animate: true,
      animationDuration: 500,
      avoidOverlap: true,
      rows: undefined,
      cols: undefined,
    },
    breadthfirst: {
      animate: true,
      animationDuration: 500,
      directed: true,
      spacingFactor: 1.5,
    },
  };

  return configs[layoutName] || configs['cose-bilkent'];
};

export default GraphViewer;
