"""
Pydantic models for PyVizAST API
"""
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class SeverityLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NodeType(str, Enum):
    """AST节点类型分类"""
    # 结构节点
    MODULE = "module"
    FUNCTION = "function"
    CLASS = "class"
    
    # 控制流
    IF = "if"
    FOR = "for"
    WHILE = "while"
    TRY = "try"
    WITH = "with"
    
    # 表达式
    CALL = "call"
    BINARY_OP = "binary_op"
    COMPARE = "compare"
    LAMBDA = "lambda"
    
    # 数据结构
    LIST = "list"
    DICT = "dict"
    SET = "set"
    TUPLE = "tuple"
    
    # 变量
    ASSIGN = "assign"
    NAME = "name"
    
    # 其他
    IMPORT = "import"
    RETURN = "return"
    YIELD = "yield"
    OTHER = "other"


class ASTNode(BaseModel):
    """AST节点可视化模型"""
    id: str
    type: NodeType
    name: Optional[str] = None
    lineno: Optional[int] = None
    col_offset: Optional[int] = None
    end_lineno: Optional[int] = None
    end_col_offset: Optional[int] = None
    
    # 可视化属性
    color: str = "#4A90D9"
    shape: str = "circle"
    size: int = 20
    
    # 图标和描述（用于学习模式）
    icon: str = "•"
    description: str = ""
    detailed_label: str = ""
    explanation: str = ""
    
    # 子节点和关系
    children: List[str] = []
    parent: Optional[str] = None
    
    # 详细信息
    docstring: Optional[str] = None
    source_code: Optional[str] = None
    attributes: Dict[str, Any] = {}


class ASTEdge(BaseModel):
    """AST节点之间的边"""
    id: str
    source: str
    target: str
    edge_type: str  # "parent-child", "call", "import", etc.
    label: Optional[str] = None


class ASTGraph(BaseModel):
    """完整的AST图结构"""
    nodes: List[ASTNode]
    edges: List[ASTEdge]
    metadata: Dict[str, Any] = {}


class CodeIssue(BaseModel):
    """代码问题"""
    id: str
    type: str  # "complexity", "performance", "code_smell", "security"
    severity: SeverityLevel
    message: str
    lineno: Optional[int] = None
    col_offset: Optional[int] = None
    end_lineno: Optional[int] = None
    end_col_offset: Optional[int] = None
    node_id: Optional[str] = None
    source_snippet: Optional[str] = None
    documentation_url: Optional[str] = None


class ComplexityMetrics(BaseModel):
    """复杂度指标"""
    cyclomatic_complexity: int = 0
    cognitive_complexity: int = 0
    lines_of_code: int = 0
    maintainability_index: float = 0.0
    halstead_volume: float = 0.0
    halstead_difficulty: float = 0.0
    
    # 函数级别
    function_count: int = 0
    class_count: int = 0
    max_nesting_depth: int = 0
    avg_function_length: float = 0.0


class PerformanceHotspot(BaseModel):
    """性能热点"""
    id: str
    node_id: str
    hotspot_type: str  # "nested_loop", "recursion", "inefficient_operation"
    description: str
    estimated_complexity: str  # Big O notation
    lineno: Optional[int] = None
    suggestion: Optional[str] = None


class OptimizationSuggestion(BaseModel):
    """优化建议"""
    id: str
    issue_id: Optional[str] = None
    node_id: Optional[str] = None
    category: str  # "performance", "readability", "security", "best_practice"
    title: str
    description: str
    before_code: Optional[str] = None
    after_code: Optional[str] = None
    estimated_improvement: Optional[str] = None  # "O(n²) -> O(n log n)"
    patch_diff: Optional[str] = None  # unified diff format
    auto_fixable: bool = False
    priority: int = 1  # 1-5, 1 is highest


class AnalysisResult(BaseModel):
    """完整分析结果"""
    # 基本信息
    filename: Optional[str] = None
    total_lines: int = 0
    
    # AST图
    ast_graph: ASTGraph
    
    # 复杂度分析
    complexity: ComplexityMetrics
    
    # 问题列表
    issues: List[CodeIssue] = []
    
    # 性能热点
    performance_hotspots: List[PerformanceHotspot] = []
    
    # 优化建议
    suggestions: List[OptimizationSuggestion] = []
    
    # 统计信息
    summary: Dict[str, Any] = {}


class CodeInput(BaseModel):
    """代码输入模型"""
    code: str
    filename: Optional[str] = None
    options: Dict[str, Any] = {}


class LearningModeResult(BaseModel):
    """学习模式结果"""
    node_id: str
    explanation: str
    python_doc: Optional[str] = None
    examples: List[str] = []
    related_concepts: List[str] = []


class ChallengeResult(BaseModel):
    """挑战模式结果"""
    challenge_id: str
    score: int
    max_score: int
    found_issues: List[str]
    missed_issues: List[str]
    feedback: str
