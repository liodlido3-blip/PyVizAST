import React from 'react';

/**
 * Loading overlay with optional progress display
 * @param {Object} props
 * @param {Object} props.progress - Progress state { stage, progress, message, details }
 */
function LoadingOverlay({ progress }) {
  const hasProgress = progress && typeof progress.progress === 'number';
  const progressPercent = hasProgress ? Math.round(progress.progress) : 0;
  const progressMessage = progress?.message || 'Analyzing code...';
  const progressStage = progress?.stage || '';
  
  // Get stage icon
  const getStageIcon = () => {
    switch (progressStage) {
      case 'uploading':
        return (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
        );
      case 'scanning':
        return (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
        );
      case 'parsing':
      case 'analyzing':
        return (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="16 18 22 12 16 6" />
            <polyline points="8 6 2 12 8 18" />
          </svg>
        );
      case 'dependencies':
        return (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="3" />
            <circle cx="4" cy="6" r="2" />
            <circle cx="20" cy="6" r="2" />
            <circle cx="4" cy="18" r="2" />
            <circle cx="20" cy="18" r="2" />
            <line x1="6" y1="6" x2="9" y2="10" />
            <line x1="18" y1="6" x2="15" y2="10" />
            <line x1="6" y1="18" x2="9" y2="14" />
            <line x1="18" y1="18" x2="15" y2="14" />
          </svg>
        );
      case 'finalizing':
        return (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
            <polyline points="22 4 12 14.01 9 11.01" />
          </svg>
        );
      default:
        return null;
    }
  };
  
  return (
    <div className="loading-overlay">
      <div className="loading-content">
        <div className="loading-spinner">
          <div className="spinner-ring"></div>
          <div className="spinner-ring"></div>
          <div className="spinner-ring"></div>
        </div>
        
        {hasProgress ? (
          <div className="loading-progress">
            <div className="progress-header">
              {getStageIcon()}
              <span className="progress-stage">{progressStage}</span>
            </div>
            <h3>{progressPercent}%</h3>
            <p>{progressMessage}</p>
            <div className="progress-bar-container">
              <div 
                className="progress-bar" 
                style={{ width: `${progressPercent}%` }}
              />
            </div>
            {progress?.details?.current_file && (
              <p className="progress-detail">{progress.details.current_file}</p>
            )}
            {progress?.details?.total_files && (
              <p className="progress-files">
                {progress.details.file_index || 0} / {progress.details.total_files} files
              </p>
            )}
          </div>
        ) : (
          <>
            <h3>Analyzing code...</h3>
            <p>Parsing AST structure and detecting issues</p>
          </>
        )}
      </div>
    </div>
  );
}

export default LoadingOverlay;
