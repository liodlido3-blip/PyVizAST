"""
Project-level analysis module for PyVizAST
Provides cross-file analysis capabilities including:
- Project scanning and file discovery
- Module dependency graph construction
- Circular dependency detection
- Unused export detection
- Project-level metrics aggregation
"""

from .scanner import ProjectScanner
from .dependency import DependencyAnalyzer
from .cycle_detector import CycleDetector
from .symbol_extractor import SymbolExtractor
from .unused_exports import UnusedExportDetector
from .metrics import ProjectMetricsAggregator
from .models import (
    ProjectScanResult,
    ProjectAnalysisResult,
    FileAnalysisResult,
    FileSummary,
    FileInfo,
    DependencyGraph,
    GlobalIssue,
    ProjectMetrics,
    ImportInfo,
    ExportInfo,
    DependencyEdge,
)

__all__ = [
    'ProjectScanner',
    'DependencyAnalyzer',
    'CycleDetector',
    'SymbolExtractor',
    'UnusedExportDetector',
    'ProjectMetricsAggregator',
    'ProjectScanResult',
    'ProjectAnalysisResult',
    'FileAnalysisResult',
    'FileSummary',
    'FileInfo',
    'DependencyGraph',
    'GlobalIssue',
    'ProjectMetrics',
    'ImportInfo',
    'ExportInfo',
    'DependencyEdge',
]
