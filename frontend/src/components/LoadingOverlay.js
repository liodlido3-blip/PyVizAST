import React from 'react';

function LoadingOverlay() {
  return (
    <div className="loading-overlay">
      <div className="loading-content">
        <div className="loading-spinner">
          <div className="spinner-ring"></div>
          <div className="spinner-ring"></div>
          <div className="spinner-ring"></div>
        </div>
        <h3>正在分析代码...</h3>
        <p>解析AST结构并检测问题</p>
      </div>
    </div>
  );
}

export default LoadingOverlay;
