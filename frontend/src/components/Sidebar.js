import React from 'react';
import {
  GitBranch,
  Activity,
  Shield,
  Lightbulb,
  BookOpen,
  Trophy
} from 'lucide-react';

function Sidebar({ isOpen, activeTab, onTabChange, analysisResult }) {
  const tabs = [
    { id: 'ast', label: 'AST可视化', icon: <GitBranch size={18} /> },
    { id: 'complexity', label: '复杂度分析', icon: <Activity size={18} /> },
    { id: 'performance', label: '性能检测', icon: <Activity size={18} /> },
    { id: 'security', label: '安全扫描', icon: <Shield size={18} /> },
    { id: 'suggestions', label: '优化建议', icon: <Lightbulb size={18} /> },
    { id: 'learn', label: '学习模式', icon: <BookOpen size={18} /> },
    { id: 'challenges', label: '挑战模式', icon: <Trophy size={18} /> },
  ];

  const getTabCount = (tabId) => {
    if (!analysisResult) return null;
    
    switch (tabId) {
      case 'complexity':
        return analysisResult.issues?.filter(i => i.type === 'complexity').length || 0;
      case 'performance':
        return analysisResult.performance_hotspots?.length || 0;
      case 'security':
        return analysisResult.issues?.filter(i => i.type === 'security').length || 0;
      case 'suggestions':
        return analysisResult.suggestions?.length || 0;
      default:
        return null;
    }
  };

  return (
    <aside className={`sidebar ${isOpen ? 'open' : 'closed'}`}>
      <nav className="sidebar-nav">
        {tabs.map((tab) => {
          const count = getTabCount(tab.id);
          const isActive = activeTab === tab.id;
          
          return (
            <button
              key={tab.id}
              className={`sidebar-tab ${isActive ? 'active' : ''}`}
              onClick={() => onTabChange(tab.id)}
            >
              <span className="tab-icon">{tab.icon}</span>
              <span className="tab-label">{tab.label}</span>
              {count !== null && count > 0 && (
                <span className="tab-count">{count}</span>
              )}
            </button>
          );
        })}
      </nav>
      
      {analysisResult && (
        <div className="sidebar-stats">
          <h4>分析摘要</h4>
          <div className="stats-grid">
            <div className="stat-item">
              <span className="stat-value">{analysisResult.total_lines}</span>
              <span className="stat-label">代码行数</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{analysisResult.complexity?.cyclomatic_complexity || 0}</span>
              <span className="stat-label">圈复杂度</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{analysisResult.summary?.total_issues || 0}</span>
              <span className="stat-label">问题总数</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{analysisResult.ast_graph?.metadata?.total_nodes || 0}</span>
              <span className="stat-label">AST节点</span>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}

export default Sidebar;
