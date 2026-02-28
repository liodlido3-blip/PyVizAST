import React from 'react';

function Header({ onAnalyze, onToggleSidebar, isLoading, theme, onThemeChange }) {
  return (
    <header className="header">
      <div className="header-left">
        <button className="btn btn-ghost menu-toggle" onClick={onToggleSidebar}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 12h18M3 6h18M3 18h18" />
          </svg>
        </button>
        
        <div className="logo">
          <span className="logo-icon">🔬</span>
          <span className="logo-text">PyVizAST</span>
        </div>
      </div>
      
      <div className="header-center">
        <nav className="header-nav">
          <a href="#features" className="nav-link">功能</a>
          <a href="#docs" className="nav-link">文档</a>
          <a href="https://github.com/ChidcGithub/PyVizAST" target="_blank" rel="noopener noreferrer" className="nav-link">
            GitHub
          </a>
        </nav>
      </div>
      
      <div className="header-right">
        <button 
          className="btn btn-ghost theme-toggle"
          onClick={() => onThemeChange(theme === 'dark' ? 'light' : 'dark')}
          title={theme === 'dark' ? '切换到亮色主题' : '切换到暗色主题'}
        >
          {theme === 'dark' ? '☀️' : '🌙'}
        </button>
        
        <button 
          className="btn btn-primary analyze-btn"
          onClick={onAnalyze}
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <span className="spinner"></span>
              分析中...
            </>
          ) : (
            <>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="5 3 19 12 5 21 5 3" />
              </svg>
              分析代码
            </>
          )}
        </button>
      </div>
    </header>
  );
}

export default Header;
