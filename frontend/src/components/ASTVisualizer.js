import React, { useEffect, useRef, useState } from 'react';

function ASTVisualizer({ graph, theme }) {
  const containerRef = useRef(null);
  const cyRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [zoom, setZoom] = useState(1);

  useEffect(() => {
    if (!graph || !containerRef.current) return;

    const loadCytoscape = async () => {
      const cytoscape = (await import('cytoscape')).default;
      const dagre = (await import('cytoscape-dagre')).default;
      
      cytoscape.use(dagre);

      // 清除旧的实例
      if (cyRef.current) {
        cyRef.current.destroy();
      }

      // 准备节点和边
      const elements = {
        nodes: graph.nodes.map(node => ({
          data: {
            id: node.id,
            label: node.name || node.type,
            type: node.type,
            color: node.color,
            size: node.size,
            lineno: node.lineno,
            docstring: node.docstring,
            source_code: node.source_code,
          }
        })),
        edges: graph.edges.map(edge => ({
          data: {
            id: edge.id,
            source: edge.source,
            target: edge.target,
            type: edge.edge_type,
          }
        }))
      };

      // 创建Cytoscape实例
      const cy = cytoscape({
        container: containerRef.current,
        elements: elements,
        style: getCytoscapeStyles(theme),
        layout: {
          name: 'dagre',
          rankDir: 'TB',
          nodeSep: 50,
          rankSep: 80,
          padding: 30,
        },
        userZoomingEnabled: true,
        userPanningEnabled: true,
        boxSelectionEnabled: true,
        minZoom: 0.2,
        maxZoom: 3,
      });

      cyRef.current = cy;

      // 节点点击事件
      cy.on('tap', 'node', (evt) => {
        const node = evt.target;
        const nodeData = node.data();
        
        setSelectedNode({
          id: nodeData.id,
          type: nodeData.type,
          name: nodeData.label,
          lineno: nodeData.lineno,
          docstring: nodeData.docstring,
          sourceCode: nodeData.source_code,
        });

        // 高亮选中节点
        cy.elements().removeClass('highlighted');
        node.addClass('highlighted');
        node.connectedEdges().addClass('highlighted');
      });

      // 点击空白处取消选中
      cy.on('tap', (evt) => {
        if (evt.target === cy) {
          setSelectedNode(null);
          cy.elements().removeClass('highlighted');
        }
      });

      // 监听缩放
      cy.on('zoom', () => {
        setZoom(cy.zoom());
      });
    };

    loadCytoscape();

    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
      }
    };
  }, [graph, theme]);

  const handleZoomIn = () => {
    if (cyRef.current) {
      cyRef.current.zoom(cyRef.current.zoom() * 1.2);
    }
  };

  const handleZoomOut = () => {
    if (cyRef.current) {
      cyRef.current.zoom(cyRef.current.zoom() / 1.2);
    }
  };

  const handleFit = () => {
    if (cyRef.current) {
      cyRef.current.fit(undefined, 30);
    }
  };

  return (
    <div className="ast-visualizer">
      <div className="visualizer-toolbar">
        <div className="toolbar-left">
          <span className="toolbar-title">AST 图结构</span>
          <span className="node-count">
            {graph?.nodes?.length || 0} 节点 · {graph?.edges?.length || 0} 边
          </span>
        </div>
        <div className="toolbar-right">
          <button className="btn btn-ghost" onClick={handleZoomOut} title="缩小">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
              <line x1="8" y1="11" x2="14" y2="11" />
            </svg>
          </button>
          <span className="zoom-level">{Math.round(zoom * 100)}%</span>
          <button className="btn btn-ghost" onClick={handleZoomIn} title="放大">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
              <line x1="11" y1="8" x2="11" y2="14" />
              <line x1="8" y1="11" x2="14" y2="11" />
            </svg>
          </button>
          <button className="btn btn-ghost" onClick={handleFit} title="适应窗口">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7" />
            </svg>
          </button>
        </div>
      </div>
      
      <div className="visualizer-content">
        <div className="cytoscape-container" ref={containerRef}></div>
        
        {selectedNode && (
          <div className="node-detail-panel">
            <div className="panel-header">
              <h4>{selectedNode.type}</h4>
              {selectedNode.name && <span className="node-name">{selectedNode.name}</span>}
            </div>
            
            <div className="panel-body">
              {selectedNode.lineno && (
                <div className="detail-item">
                  <span className="detail-label">行号</span>
                  <span className="detail-value">{selectedNode.lineno}</span>
                </div>
              )}
              
              {selectedNode.docstring && (
                <div className="detail-item">
                  <span className="detail-label">文档字符串</span>
                  <p className="docstring">{selectedNode.docstring}</p>
                </div>
              )}
              
              {selectedNode.sourceCode && (
                <div className="detail-item">
                  <span className="detail-label">源代码</span>
                  <pre className="source-code">{selectedNode.sourceCode}</pre>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
      
      <div className="visualizer-legend">
        <div className="legend-item">
          <span className="legend-color" style={{ background: '#1565C0' }}></span>
          <span>函数</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ background: '#7B1FA2' }}></span>
          <span>类</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ background: '#F57C00' }}></span>
          <span>控制流</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ background: '#0288D1' }}></span>
          <span>调用</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ background: '#616161' }}></span>
          <span>赋值</span>
        </div>
      </div>
    </div>
  );
}

function getCytoscapeStyles(theme) {
  const isDark = theme === 'dark';
  
  return [
    {
      selector: 'node',
      style: {
        'background-color': 'data(color)',
        'label': 'data(label)',
        'width': 'data(size)',
        'height': 'data(size)',
        'font-size': '12px',
        'font-family': 'Inter, sans-serif',
        'color': isDark ? '#ffffff' : '#1a1a2e',
        'text-valign': 'center',
        'text-halign': 'center',
        'text-outline-color': isDark ? '#0f0f1a' : '#ffffff',
        'text-outline-width': '2px',
        'border-width': '2px',
        'border-color': 'data(color)',
        'border-opacity': '0.5',
        'transition-property': 'width, height, border-width',
        'transition-duration': '0.2s',
      }
    },
    {
      selector: 'node.highlighted',
      style: {
        'border-width': '4px',
        'border-color': '#6366f1',
        'border-opacity': '1',
        'width': 'data(size) * 1.2',
        'height': 'data(size) * 1.2',
      }
    },
    {
      selector: 'node[type="function"]',
      style: {
        'shape': 'roundrectangle',
        'width': 'data(size) * 2',
      }
    },
    {
      selector: 'node[type="class"]',
      style: {
        'shape': 'roundrectangle',
        'width': 'data(size) * 2',
      }
    },
    {
      selector: 'node[type="if"], node[type="for"], node[type="while"]',
      style: {
        'shape': 'diamond',
      }
    },
    {
      selector: 'edge',
      style: {
        'width': '2px',
        'line-color': isDark ? '#3a3a5a' : '#d0d0d0',
        'target-arrow-color': isDark ? '#3a3a5a' : '#d0d0d0',
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier',
        'arrow-scale': '0.8',
      }
    },
    {
      selector: 'edge.highlighted',
      style: {
        'width': '3px',
        'line-color': '#6366f1',
        'target-arrow-color': '#6366f1',
      }
    },
    {
      selector: 'edge[type="call"]',
      style: {
        'line-color': '#8b5cf6',
        'target-arrow-color': '#8b5cf6',
        'line-style': 'dashed',
      }
    },
  ];
}

export default ASTVisualizer;
