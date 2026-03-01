import React, { useState, useCallback, useEffect } from 'react';
import {
  Wand2,
  Check,
  ChevronRight,
  ChevronDown,
  AlertCircle,
  CheckCircle,
  Loader,
  Code,
  ArrowRight,
  Copy,
  CheckCheck
} from 'lucide-react';
import { generatePatches } from '../api';

/**
 * 补丁应用面板组件
 * 显示可自动修复的优化建议,并允许用户预览和应用补丁
 */
function PatchPanel({ code, onApplyPatch }) {
  const [patches, setPatches] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedPatch, setExpandedPatch] = useState(null);
  const [appliedPatches, setAppliedPatches] = useState(new Set());
  const [copiedPatch, setCopiedPatch] = useState(null);

  // 获取补丁列表
  useEffect(() => {
    if (!code || code.trim().length === 0) {
      setPatches([]);
      return;
    }

    const fetchPatches = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const result = await generatePatches(code);
        setPatches(result.patches || []);
      } catch (err) {
        setError(err.message || '获取补丁失败');
        setPatches([]);
      } finally {
        setLoading(false);
      }
    };

    // 延迟获取,避免频繁请求
    const timer = setTimeout(fetchPatches, 300);
    return () => clearTimeout(timer);
  }, [code]);

  // 切换补丁展开状态
  const togglePatch = useCallback((patchId) => {
    setExpandedPatch(prev => prev === patchId ? null : patchId);
  }, []);

  // 应用补丁
  const handleApply = useCallback((patch) => {
    if (onApplyPatch) {
      // 解析补丁获取修改后的代码
      const fixedCode = applyPatchToCode(code, patch.patch);
      if (fixedCode) {
        onApplyPatch(fixedCode);
        setAppliedPatches(prev => new Set([...prev, patch.suggestion_id]));
      }
    }
  }, [code, onApplyPatch]);

  // 复制补丁
  const handleCopy = useCallback(async (patchId, patchContent) => {
    try {
      await navigator.clipboard.writeText(patchContent);
      setCopiedPatch(patchId);
      setTimeout(() => setCopiedPatch(null), 2000);
    } catch (err) {
      console.error('复制失败:', err);
    }
  }, []);

  // 渲染补丁差异
  const renderDiff = (patchContent) => {
    if (!patchContent) return null;
    
    const lines = patchContent.split('\n');
    
    return (
      <div className="patch-diff">
        {lines.map((line, index) => {
          let className = 'diff-line';
          
          if (line.startsWith('+++') || line.startsWith('---')) {
            className += ' diff-header';
          } else if (line.startsWith('@@')) {
            className += ' diff-hunk';
          } else if (line.startsWith('+')) {
            className += ' diff-add';
          } else if (line.startsWith('-')) {
            className += ' diff-remove';
          } else if (line.startsWith(' ')) {
            className += ' diff-context';
          }
          
          return (
            <div key={index} className={className}>
              <span className="line-content">{line}</span>
            </div>
          );
        })}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="patch-panel loading">
        <Loader className="spinner" size={24} />
        <span>正在分析可修复的问题...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="patch-panel error">
        <AlertCircle size={20} />
        <span>{error}</span>
      </div>
    );
  }

  if (patches.length === 0) {
    return (
      <div className="patch-panel empty">
        <CheckCircle size={48} className="success-icon" />
        <h4>无需自动修复</h4>
        <p>代码中没有可自动修复的问题</p>
      </div>
    );
  }

  return (
    <div className="patch-panel">
      <div className="patch-header">
        <Wand2 size={18} />
        <h3>自动修复建议</h3>
        <span className="patch-count">{patches.length} 项可修复</span>
      </div>

      <div className="patch-list">
        {patches.map((patch) => {
          const isExpanded = expandedPatch === patch.suggestion_id;
          const isApplied = appliedPatches.has(patch.suggestion_id);
          
          return (
            <div 
              key={patch.suggestion_id} 
              className={`patch-item ${isExpanded ? 'expanded' : ''} ${isApplied ? 'applied' : ''}`}
            >
              <div 
                className="patch-item-header"
                onClick={() => togglePatch(patch.suggestion_id)}
              >
                <div className="patch-item-title">
                  {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                  <span className="patch-category">{getCategoryIcon(patch.category)}</span>
                  <span className="patch-title">{patch.title}</span>
                </div>
                <div className="patch-item-actions">
                  {isApplied ? (
                    <span className="applied-badge">
                      <Check size={14} />
                      已应用
                    </span>
                  ) : (
                    <span className="auto-fix-badge">
                      <Wand2 size={12} />
                      可修复
                    </span>
                  )}
                </div>
              </div>

              {isExpanded && (
                <div className="patch-item-body">
                  <p className="patch-description">{patch.description}</p>
                  
                  {patch.patch && (
                    <div className="patch-diff-container">
                      <div className="patch-diff-header">
                        <span>
                          <Code size={14} />
                          补丁预览 (Unified Diff)
                        </span>
                        <button 
                          className="btn-copy"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleCopy(patch.suggestion_id, patch.patch);
                          }}
                        >
                          {copiedPatch === patch.suggestion_id ? (
                            <>
                              <CheckCheck size={14} />
                              已复制
                            </>
                          ) : (
                            <>
                              <Copy size={14} />
                              复制
                            </>
                          )}
                        </button>
                      </div>
                      {renderDiff(patch.patch)}
                    </div>
                  )}

                  <div className="patch-actions">
                    {!isApplied && (
                      <button 
                        className="btn btn-primary btn-apply"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleApply(patch);
                        }}
                      >
                        <Wand2 size={14} />
                        应用此修复
                        <ArrowRight size={14} />
                      </button>
                    )}
                    <span className="patch-hint">
                      应用后将更新代码编辑器中的内容
                    </span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

/**
 * 解析补丁并应用到代码
 * 这是一个简化版本,实际应用应该在后端进行
 */
function applyPatchToCode(originalCode, patchContent) {
  if (!patchContent) return null;
  
  try {
    const lines = originalCode.split('\n');
    const patchLines = patchContent.split('\n');
    
    // 解析 hunks
    const hunks = [];
    let currentHunk = null;
    
    for (const line of patchLines) {
      if (line.startsWith('@@')) {
        if (currentHunk) hunks.push(currentHunk);
        
        // 解析 @@ -start,count +start,count @@
        const match = line.match(/@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@/);
        if (match) {
          currentHunk = {
            oldStart: parseInt(match[1]),
            newStart: parseInt(match[2]),
            additions: [],
            removals: [],
            context: []
          };
        }
      } else if (currentHunk) {
        if (line.startsWith('+') && !line.startsWith('+++')) {
          currentHunk.additions.push(line.substring(1));
        } else if (line.startsWith('-') && !line.startsWith('---')) {
          currentHunk.removals.push(line.substring(1));
        } else if (line.startsWith(' ') || line === '') {
          currentHunk.context.push(line.startsWith(' ') ? line.substring(1) : '');
        }
      }
    }
    
    if (currentHunk) hunks.push(currentHunk);
    
    // 从后向前应用 hunks,避免行号偏移
    hunks.sort((a, b) => b.oldStart - a.oldStart);
    
    for (const hunk of hunks) {
      const startIdx = hunk.oldStart - 1;
      const removeCount = hunk.removals.length || hunk.context.filter((_, i) => 
        i < hunk.context.length - hunk.additions.length
      ).length;
      
      // 移除旧行,添加新行
      lines.splice(startIdx, removeCount, ...hunk.additions, ...hunk.context.slice(hunk.additions.length));
    }
    
    return lines.join('\n');
  } catch (err) {
    console.error('应用补丁失败:', err);
    return null;
  }
}

// 获取分类图标
function getCategoryIcon(category) {
  const icons = {
    performance: '⚡',
    readability: '📖',
    security: '🔒',
    best_practice: '✨',
  };
  return icons[category] || '📝';
}

export default PatchPanel;
