import React, { useRef, useEffect } from 'react';

function CodeEditor({ code, onChange, theme }) {
  const editorRef = useRef(null);
  const monacoRef = useRef(null);

  useEffect(() => {
    // 动态加载Monaco Editor
    const loadMonaco = async () => {
      const monaco = await import('monaco-editor');
      monacoRef.current = monaco;
      
      if (editorRef.current && !editorRef.current.editor) {
        // 定义自定义主题
        monaco.editor.defineTheme('pyvizast-dark', {
          base: 'vs-dark',
          inherit: true,
          rules: [
            { token: 'comment', foreground: '6b6b80', fontStyle: 'italic' },
            { token: 'keyword', foreground: 'c792ea' },
            { token: 'string', foreground: 'c3e88d' },
            { token: 'number', foreground: 'f78c6c' },
            { token: 'type', foreground: '82aaff' },
            { token: 'function', foreground: '82aaff' },
            { token: 'variable', foreground: 'f07178' },
          ],
          colors: {
            'editor.background': '#1a1a2e',
            'editor.foreground': '#d4d4d4',
            'editor.lineHighlightBackground': '#252542',
            'editorLineNumber.foreground': '#4a4a6a',
            'editorLineNumber.activeForeground': '#6366f1',
            'editor.selectionBackground': '#6366f140',
            'editorCursor.foreground': '#6366f1',
            'editorIndentGuide.background': '#2a2a4a',
            'editorIndentGuide.activeBackground': '#3a3a5a',
          }
        });

        monaco.editor.defineTheme('pyvizast-light', {
          base: 'vs',
          inherit: true,
          rules: [
            { token: 'comment', foreground: '6a9955', fontStyle: 'italic' },
            { token: 'keyword', foreground: '8b5cf6' },
            { token: 'string', foreground: 'ce9178' },
            { token: 'number', foreground: 'b5cea8' },
          ],
          colors: {
            'editor.background': '#ffffff',
            'editor.foreground': '#1a1a2e',
            'editor.lineHighlightBackground': '#f5f5f5',
          }
        });

        const editor = monaco.editor.create(editorRef.current, {
          value: code,
          language: 'python',
          theme: theme === 'dark' ? 'pyvizast-dark' : 'pyvizast-light',
          fontSize: 14,
          fontFamily: "'JetBrains Mono', monospace",
          lineHeight: 22,
          padding: { top: 16, bottom: 16 },
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          automaticLayout: true,
          tabSize: 4,
          wordWrap: 'on',
          renderLineHighlight: 'all',
          cursorBlinking: 'smooth',
          cursorSmoothCaretAnimation: 'on',
          smoothScrolling: true,
          folding: true,
          foldingHighlight: true,
          bracketPairColorization: { enabled: true },
          guides: {
            bracketPairs: true,
            indentation: true,
          },
        });

        editorRef.current.editor = editor;

        editor.onDidChangeModelContent(() => {
          const newValue = editor.getValue();
          onChange(newValue);
        });
      }
    };

    loadMonaco();

    return () => {
      if (editorRef.current?.editor) {
        editorRef.current.editor.dispose();
      }
    };
  }, []);

  // 更新代码
  useEffect(() => {
    if (editorRef.current?.editor && code !== editorRef.current.editor.getValue()) {
      editorRef.current.editor.setValue(code);
    }
  }, [code]);

  // 更新主题
  useEffect(() => {
    if (editorRef.current?.editor && monacoRef.current) {
      monacoRef.current.editor.setTheme(theme === 'dark' ? 'pyvizast-dark' : 'pyvizast-light');
    }
  }, [theme]);

  return (
    <div className="code-editor">
      <div className="editor-header">
        <div className="file-tabs">
          <div className="file-tab active">
            <span className="file-icon">🐍</span>
            <span>main.py</span>
          </div>
        </div>
        <div className="editor-actions">
          <button className="btn btn-ghost" title="格式化代码">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 10H3M21 6H3M21 14H3M21 18H3" />
            </svg>
          </button>
          <button className="btn btn-ghost" title="清空">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
            </svg>
          </button>
        </div>
      </div>
      <div className="editor-container" ref={editorRef}></div>
    </div>
  );
}

export default CodeEditor;
