import React, { useState, useCallback, useEffect, useRef, Suspense, lazy } from 'react';
import CodeEditor from './components/CodeEditor';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import LoadingOverlay from './components/LoadingOverlay';
import ErrorBoundary from './components/ErrorBoundary';
import ProjectAnalysisView from './components/ProjectAnalysisView';
import ProjectVisualization from './components/ProjectVisualization';
import { analyzeCode, checkServerHealth, getApiBaseUrl } from './api';
import { setupGlobalErrorHandlers } from './utils/logger';
import './App.css';
import './components/components.css';
import './components/AnalysisPanel.css';

// Lazy load heavy components for code splitting
const ASTVisualizer = lazy(() => import('./components/ASTVisualizer'));
const ASTVisualizer3D = lazy(() => import('./components/ASTVisualizer3D'));
const AnalysisPanel = lazy(() => import('./components/AnalysisPanel'));

// Loading fallback for lazy components
const ComponentLoader = () => (
  <div className="component-loader">
    <div className="loader-spinner"></div>
    <span>Loading component...</span>
  </div>
);

// Sample code for demo
const SAMPLE_CODE = `# PyVizAST 示例代码
# 这个文件展示了各种Python语法结构

import os
from typing import List, Optional

# 全局配置
CONFIG = {
    "debug": True,
    "max_items": 100
}

class DataProcessor:
    """数据处理类"""
    
    def __init__(self, name: str):
        self.name = name
        self.data = []
    
    def process(self, items: List[int]) -> List[int]:
        """处理数据列表"""
        result = []
        
        # 嵌套循环示例
        for item in items:
            if item > 0:
                for i in range(item):
                    if i % 2 == 0:
                        result.append(i * 2)
        
        return result
    
    def calculate_average(self, numbers: List[float]) -> Optional[float]:
        """计算平均值"""
        if not numbers:
            return None
        
        total = sum(numbers)
        return total / len(numbers)


def fibonacci(n: int) -> int:
    """递归计算斐波那契数"""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


def find_duplicates(arr: List[int]) -> List[int]:
    """找出重复元素"""
    seen = set()
    duplicates = []
    
    for item in arr:
        if item in seen:
            if item not in duplicates:
                duplicates.append(item)
        else:
            seen.add(item)
    
    return duplicates


# 主函数
def main():
    processor = DataProcessor("test")
    
    # 生成测试数据
    data = [i for i in range(20)]
    
    # 处理数据
    result = processor.process(data)
    print(f"处理结果: {result[:10]}...")
    
    # 计算斐波那契
    fib = fibonacci(10)
    print(f"斐波那契(10) = {fib}")


if __name__ == "__main__":
    main()
`;


function App() {
  const [code, setCode] = useState(SAMPLE_CODE);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('ast');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [theme, setTheme] = useState('dark');
  const [viewMode, setViewMode] = useState('2d'); // '2d' or '3d'
  const [serverStatus, setServerStatus] = useState({ checking: true, connected: false });
  
  // 分析模式: 'file' 或 'project'
  const [analysisMode, setAnalysisMode] = useState('file');
  
  // 项目分析状态
  const [projectResult, setProjectResult] = useState(null);
  const [isProjectAnalyzing, setIsProjectAnalyzing] = useState(false);
  const projectAnalysisRef = useRef(null);
  
  // 项目模式下选中的文件
  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedFileIndex, setSelectedFileIndex] = useState(null);
  const [isFileEditMode, setIsFileEditMode] = useState(false);
  
  // 分割线拖动状态
  const [splitPosition, setSplitPosition] = useState(50); // 百分比
  const [isDragging, setIsDragging] = useState(false);
  const mainContentRef = useRef(null);
  
  // 用于取消请求的 AbortController
  const abortControllerRef = useRef(null);
  
  // 编辑器 ref，用于调用编辑器方法（如跳转到指定行）
  const editorRef = useRef(null);
  
  // 初始化全局错误处理器
  useEffect(() => {
    setupGlobalErrorHandlers();
  }, []);
  
  // 分割线拖动处理
  const handleMouseDown = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);
  
  const handleMouseMove = useCallback((e) => {
    if (!isDragging || !mainContentRef.current) return;
    
    const rect = mainContentRef.current.getBoundingClientRect();
    const newPosition = ((e.clientX - rect.left) / rect.width) * 100;
    
    // 限制最小和最大位置
    const clampedPosition = Math.min(Math.max(newPosition, 20), 80);
    setSplitPosition(clampedPosition);
  }, [isDragging]);
  
  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);
  
  // 添加全局鼠标事件监听
  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    }
    
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isDragging, handleMouseMove, handleMouseUp]);

  // 检查服务器连接状态
  useEffect(() => {
    const checkConnection = async () => {
      const result = await checkServerHealth();
      setServerStatus({ 
        checking: false, 
        connected: result.connected,
        error: result.error,
        hint: result.hint
      });
    };
    
    checkConnection();
    // 每30秒检查一次连接
    const interval = setInterval(checkConnection, 30000);
    return () => clearInterval(interval);
  }, []);

  // 组件卸载时取消正在进行的请求
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // 单文件分析
  const handleAnalyze = useCallback(async () => {
    // 项目模式下调用项目分析
    if (analysisMode === 'project') {
      if (projectAnalysisRef.current?.canAnalyze()) {
        projectAnalysisRef.current.analyze();
      }
      return;
    }

    if (!code.trim()) {
      setError('请输入Python代码');
      return;
    }

    // 检查服务器连接
    if (!serverStatus.connected) {
      setError(`无法连接到服务器 (${getApiBaseUrl()})。请确保后端正在运行: python run.py backend`);
      return;
    }

    // 取消之前的请求
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    // 创建新的 AbortController
    abortControllerRef.current = new AbortController();

    setIsLoading(true);
    setError(null);

    try {
      const result = await analyzeCode(code, {}, abortControllerRef.current.signal);
      setAnalysisResult(result);
    } catch (err) {
      // 如果是取消的请求，不显示错误
      if (err.name === 'AbortError' || err.name === 'CanceledError') {
        return;
      }
      // 提供更详细的错误信息
      if (err.message?.includes('Network Error') || err.message?.includes('无法连接')) {
        setError(`无法连接到服务器 (${getApiBaseUrl()})。请确保后端正在运行: python run.py backend`);
      } else {
        setError(err.message || '分析失败，请检查代码语法');
      }
    } finally {
      setIsLoading(false);
    }
  }, [code, serverStatus.connected, analysisMode]);

  // 项目分析结果回调
  const handleProjectResultChange = useCallback((result) => {
    setProjectResult(result);
  }, []);

  // 项目分析状态变化回调
  const handleProjectAnalysisStateChange = useCallback((isAnalyzing) => {
    setIsProjectAnalyzing(isAnalyzing);
    setIsLoading(isAnalyzing);
  }, []);

  // 文件选择回调（单击）
  const handleFileSelect = useCallback((fileAnalysis, index) => {
    setSelectedFile(fileAnalysis);
    setSelectedFileIndex(index);
    setIsFileEditMode(false);
  }, []);

  // 文件双击回调（进入编辑模式）
  const handleFileDoubleClick = useCallback((fileAnalysis, index) => {
    setSelectedFile(fileAnalysis);
    setSelectedFileIndex(index);
    setIsFileEditMode(true);
    // 设置文件内容到编辑器 (content 在 fileAnalysis 根级别)
    if (fileAnalysis?.content) {
      setCode(fileAnalysis.content);
    }
  }, []);

  // 退出编辑模式回调
  const handleExitEditMode = useCallback(() => {
    setIsFileEditMode(false);
    setSelectedFile(null);
    setSelectedFileIndex(null);
  }, []);

  // 切换分析模式
  const handleAnalysisModeChange = useCallback((mode) => {
    setAnalysisMode(mode);
    setError(null);
    // 切换模式时清除之前的结果
    if (mode === 'file') {
      setProjectResult(null);
    } else {
      setAnalysisResult(null);
    }
  }, []);

  const handleCodeChange = useCallback((newCode) => {
    setCode(newCode);
    setAnalysisResult(null);
    setError(null);
  }, []);
  
  /**
   * 跳转到编辑器指定行
   * @param {number} lineNumber - 行号（从1开始）
   * @param {number} [endLine] - 可选的结束行号
   */
  const handleGoToLine = useCallback((lineNumber, endLine) => {
    if (editorRef.current) {
      editorRef.current.goToLine(lineNumber, 1, endLine);
    }
  }, []);

  return (
    <div className={`app ${theme}`}>
      {(isLoading || isProjectAnalyzing) && <LoadingOverlay />}
      
      <Header 
        onAnalyze={handleAnalyze}
        onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        isLoading={isLoading || isProjectAnalyzing}
        theme={theme}
        onThemeChange={setTheme}
        analysisMode={analysisMode}
        onAnalysisModeChange={handleAnalysisModeChange}
      />
      
      <div className="app-body">
        <Sidebar 
          isOpen={sidebarOpen}
          activeTab={activeTab}
          onTabChange={setActiveTab}
          analysisResult={analysisResult}
          viewMode={viewMode}
          onViewModeChange={setViewMode}
        />
        
        {/* 项目分析模式 */}
        {analysisMode === 'project' ? (
          <main className="main-content project-mode" ref={mainContentRef}
            style={{ 
              '--split-position': `${splitPosition}%`,
              cursor: isDragging ? 'col-resize' : 'default'
            }}>
            <div className="project-left-panel" style={{ width: `calc(var(--split-position, 35%) - 4px)` }}>
              <ProjectAnalysisView
                ref={projectAnalysisRef}
                theme={theme}
                activeTab={activeTab}
                onAnalysisStateChange={handleProjectAnalysisStateChange}
                onResultChange={handleProjectResultChange}
                onFileSelect={handleFileSelect}
                onFileDoubleClick={handleFileDoubleClick}
                editedFilePath={selectedFile?.file?.relative_path}
              />
            </div>
            
            <div 
              className={`resize-divider ${isDragging ? 'dragging' : ''}`}
              onMouseDown={handleMouseDown}
            >
              <div className="resize-handle">
                <svg width="4" height="24" viewBox="0 0 4 24" fill="none">
                  <circle cx="2" cy="6" r="1" fill="currentColor" />
                  <circle cx="2" cy="12" r="1" fill="currentColor" />
                  <circle cx="2" cy="18" r="1" fill="currentColor" />
                </svg>
              </div>
            </div>
            
            <div className="visualization-panel">
              {/* 编辑模式 - 显示编辑器 */}
              {isFileEditMode && selectedFile ? (
                <div className="project-edit-mode">
                  <div className="project-edit-header">
                    <button className="exit-edit-btn" onClick={handleExitEditMode} title="退出编辑">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <line x1="18" y1="6" x2="6" y2="18" />
                        <line x1="6" y1="6" x2="18" y2="18" />
                      </svg>
                    </button>
                    <div className="edit-file-info">
                      <span className="edit-file-name">{selectedFile?.file?.relative_path?.split('/').pop() || '文件'}</span>
                      <span className="edit-file-path">{selectedFile?.file?.relative_path}</span>
                    </div>
                  </div>
                  <div className="project-edit-content">
                    <CodeEditor 
                      ref={editorRef}
                      code={code}
                      onChange={handleCodeChange}
                      theme={theme}
                    />
                  </div>
                </div>
              ) : (
                <>
                  {!serverStatus.checking && !serverStatus.connected && (
                    <div className="server-status-error">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <rect x="2" y="2" width="20" height="8" rx="2" ry="2" />
                        <rect x="2" y="14" width="20" height="8" rx="2" ry="2" />
                        <line x1="6" y1="6" x2="6.01" y2="6" />
                        <line x1="6" y1="18" x2="6.01" y2="18" />
                      </svg>
                      <div className="status-content">
                        <strong>无法连接到后端服务器</strong>
                        <p>API地址: {getApiBaseUrl()}</p>
                        <p className="status-hint">请在终端运行: <code>python run.py backend</code></p>
                      </div>
                    </div>
                  )}
                  
                  {error && (
                    <div className="error-message">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="10" />
                        <line x1="12" y1="8" x2="12" y2="12" />
                        <line x1="12" y1="16" x2="12.01" y2="16" />
                      </svg>
                      {error}
                    </div>
                  )}
                  
                  <ErrorBoundary>
                    {projectResult ? (
                      activeTab === 'ast' ? (
                        <ProjectVisualization 
                          projectResult={projectResult}
                          theme={theme}
                          viewMode={viewMode}
                        />
                      ) : (
                        <Suspense fallback={<ComponentLoader />}>
                          <AnalysisPanel 
                            result={{
                              issues: [
                                ...(projectResult.global_issues || []),
                                ...(projectResult.files?.flatMap(f => f.issues || []) || [])
                              ],
                              suggestions: projectResult.files?.flatMap(f => f.suggestions || []) || [],
                              performance_hotspots: projectResult.files?.flatMap(f => f.performance_hotspots || []) || [],
                              complexity: {
                                cyclomatic_complexity: projectResult.metrics?.avg_complexity || 0,
                                cognitive_complexity: 0,
                                maintainability_index: projectResult.metrics?.avg_maintainability || 0,
                                max_nesting_depth: 0,
                                lines_of_code: projectResult.metrics?.total_lines || 0,
                                function_count: projectResult.metrics?.total_functions || 0,
                                class_count: projectResult.metrics?.total_classes || 0,
                                avg_function_length: 0,
                                halstead_volume: 0,
                                halstead_difficulty: 0,
                              },
                              summary: {
                                total_issues: (projectResult.global_issues?.length || 0) + 
                                  (projectResult.files?.reduce((sum, f) => sum + (f.summary?.issue_count || 0), 0) || 0),
                                project_stats: projectResult.metrics
                              }
                            }}
                            activeTab={activeTab}
                            code=""
                            onApplyPatch={() => {}}
                            projectMode={true}
                            projectResult={projectResult}
                          />
                        </Suspense>
                      )
                    ) : (
                      <div className="placeholder">
                        <div className="placeholder-icon">
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
                          </svg>
                        </div>
                        <h3>Project Analysis</h3>
                        <p>Upload a ZIP file and click Analyze to begin</p>
                        <p className="placeholder-hint">
                          Dependency graph, circular dependency detection, unused exports
                        </p>
                      </div>
                    )}
                  </ErrorBoundary>
                </>
              )}
            </div>
          </main>
        ) : (
        /* 单文件分析模式 */
        <main 
          className="main-content" 
          ref={mainContentRef}
          style={{ 
            '--split-position': `${splitPosition}%`,
            cursor: isDragging ? 'col-resize' : 'default'
          }}
        >
          <div className="editor-panel">
            <CodeEditor 
              ref={editorRef}
              code={code}
              onChange={handleCodeChange}
              theme={theme}
            />
          </div>
          
          {/* 可拖动的分割线 */}
          <div 
            className={`resize-divider ${isDragging ? 'dragging' : ''}`}
            onMouseDown={handleMouseDown}
          >
            <div className="resize-handle">
              <svg width="4" height="24" viewBox="0 0 4 24" fill="none">
                <circle cx="2" cy="6" r="1" fill="currentColor" />
                <circle cx="2" cy="12" r="1" fill="currentColor" />
                <circle cx="2" cy="18" r="1" fill="currentColor" />
              </svg>
            </div>
          </div>
          
          <div className="visualization-panel">
            {/* 服务器连接状态 */}
            {!serverStatus.checking && !serverStatus.connected && (
              <div className="server-status-error">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="2" y="2" width="20" height="8" rx="2" ry="2" />
                  <rect x="2" y="14" width="20" height="8" rx="2" ry="2" />
                  <line x1="6" y1="6" x2="6.01" y2="6" />
                  <line x1="6" y1="18" x2="6.01" y2="18" />
                </svg>
                <div className="status-content">
                  <strong>无法连接到后端服务器</strong>
                  <p>API地址: {getApiBaseUrl()}</p>
                  <p className="status-hint">请在终端运行: <code>python run.py backend</code></p>
                </div>
              </div>
            )}
            
            {error && (
              <div className="error-message">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
                {error}
              </div>
            )}
            
            <ErrorBoundary>
              {analysisResult ? (
                activeTab === 'ast' ? (
                  <Suspense fallback={<ComponentLoader />}>
                    {viewMode === '3d' ? (
                      <ASTVisualizer3D 
                        graph={analysisResult.ast_graph}
                        theme={theme}
                        onGoToLine={handleGoToLine}
                      />
                    ) : (
                      <ASTVisualizer 
                        graph={analysisResult.ast_graph}
                        theme={theme}
                        onGoToLine={handleGoToLine}
                      />
                    )}
                  </Suspense>
                ) : (
                  <Suspense fallback={<ComponentLoader />}>
                    <AnalysisPanel 
                      result={analysisResult}
                      activeTab={activeTab}
                      code={code}
                      onApplyPatch={handleCodeChange}
                    />
                  </Suspense>
                )
              ) : (
                <div className="placeholder">
                  <div className="placeholder-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <polyline points="14 2 14 8 20 8" />
                      <line x1="16" y1="13" x2="8" y2="13" />
                      <line x1="16" y1="17" x2="8" y2="17" />
                      <polyline points="10 9 9 9 8 9" />
                    </svg>
                  </div>
                  <h3>PyVizAST</h3>
                  <p>Enter Python code and click Analyze to begin</p>
                  <p className="placeholder-hint">
                    AST visualization, complexity analysis, performance detection, security scanning
                  </p>
                </div>
              )}
            </ErrorBoundary>
          </div>
        </main>
        )}
      </div>
    </div>
  );
}

export default App;
