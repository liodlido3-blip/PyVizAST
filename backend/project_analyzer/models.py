"""
Data models for project-level analysis
统一使用 Pydantic BaseModel 以保持类型系统一致性
"""
from typing import Optional, List, Dict, Any, Set
from pydantic import BaseModel, Field, ConfigDict


class FileInfo(BaseModel):
    """文件信息"""
    model_config = ConfigDict(frozen=False)
    
    path: str
    relative_path: str
    size: int = 0
    line_count: int = 0
    is_test: bool = False
    is_init: bool = False
    is_main: bool = False


class ImportInfo(BaseModel):
    """导入信息"""
    model_config = ConfigDict(frozen=False)
    
    module: str
    names: List[str] = Field(default_factory=list)
    alias: Optional[str] = None
    is_relative: bool = False
    level: int = 0  # 相对导入层级
    lineno: int = 0


class ExportInfo(BaseModel):
    """导出信息（函数、类、变量）"""
    model_config = ConfigDict(frozen=False)
    
    name: str
    type: str  # 'function', 'class', 'variable', 'constant'
    lineno: int = 0
    is_public: bool = True
    is_used: bool = False
    used_in: List[str] = Field(default_factory=list)  # 使用 List 替代 Set 以支持 JSON 序列化


class DependencyEdge(BaseModel):
    """依赖边"""
    model_config = ConfigDict(frozen=False)
    
    source: str
    target: str
    import_type: str  # 'import', 'from_import', 'relative'
    imported_names: List[str] = Field(default_factory=list)
    lineno: int = 0


class DependencyGraph(BaseModel):
    """依赖图模型"""
    nodes: List[str] = Field(default_factory=list, description="所有模块节点")
    edges: List[Dict[str, Any]] = Field(default_factory=list, description="依赖边")
    adjacency_list: Dict[str, List[str]] = Field(default_factory=dict, description="邻接表")


class GlobalIssue(BaseModel):
    """全局问题（跨文件）"""
    issue_type: str = Field(..., description="问题类型")
    severity: str = Field(default="warning", description="严重程度")
    message: str = Field(..., description="问题描述")
    locations: List[Dict[str, Any]] = Field(default_factory=list, description="相关位置")
    suggestion: Optional[str] = Field(None, description="修复建议")


class FileSummary(BaseModel):
    """文件分析摘要"""
    issue_count: int = 0
    cyclomatic_complexity: int = 0
    lines_of_code: int = 0
    function_count: int = 0
    class_count: int = 0
    maintainability_index: float = 0.0


class FileAnalysisResult(BaseModel):
    """单个文件的分析结果"""
    file: FileInfo
    content: str = ""  # 文件内容
    summary: FileSummary = Field(default_factory=FileSummary)
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    complexity: Dict[str, Any] = Field(default_factory=dict)
    performance_hotspots: List[Dict[str, Any]] = Field(default_factory=list)
    suggestions: List[Dict[str, Any]] = Field(default_factory=list)


class ProjectMetrics(BaseModel):
    """项目级指标"""
    total_files: int = 0
    total_lines: int = 0
    total_functions: int = 0
    total_classes: int = 0
    avg_complexity: float = 0.0
    avg_maintainability: float = 0.0
    max_complexity_file: Optional[str] = None
    max_complexity_value: int = 0
    dependency_count: int = 0
    circular_dependency_count: int = 0
    unused_export_count: int = 0
    test_coverage_estimate: float = 0.0


class ProjectScanResult(BaseModel):
    """项目扫描结果"""
    project_name: str
    total_files: int = 0
    total_size: int = 0
    file_paths: List[str] = Field(default_factory=list)
    file_infos: List[FileInfo] = Field(default_factory=list)
    skipped_count: int = 0
    skipped_files: List[str] = Field(default_factory=list)
    scan_time_ms: float = 0.0


class ProjectAnalysisResult(BaseModel):
    """完整项目分析结果"""
    scan_result: ProjectScanResult
    files: List[FileAnalysisResult] = Field(default_factory=list)
    dependencies: Dict[str, Any] = Field(default_factory=dict)
    global_issues: List[GlobalIssue] = Field(default_factory=list)
    metrics: ProjectMetrics = Field(default_factory=ProjectMetrics)
    analysis_time_ms: float = 0.0
