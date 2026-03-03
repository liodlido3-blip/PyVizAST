"""
Project Metrics Aggregator - 聚合项目级指标
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .models import ProjectMetrics, FileAnalysisResult, ProjectScanResult
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ProjectMetricsAggregator:
    """项目指标聚合器"""
    
    def __init__(self):
        self.reset()
    
    def reset(self) -> None:
        """重置聚合器状态"""
        self.total_files = 0
        self.total_lines = 0
        self.total_functions = 0
        self.total_classes = 0
        self.total_complexity = 0
        self.total_maintainability = 0.0
        self.complexity_by_file: Dict[str, int] = {}
        self.file_count = 0  # 用于计算平均值
    
    def aggregate(self, file_results: List[FileAnalysisResult],
                  scan_result: ProjectScanResult,
                  global_issues: List[Any]) -> ProjectMetrics:
        """
        聚合所有文件的分析结果
        
        Args:
            file_results: 文件分析结果列表
            scan_result: 项目扫描结果
            global_issues: 全局问题列表
        
        Returns:
            项目级指标
        """
        self.reset()
        
        # 基础统计
        self.total_files = scan_result.total_files
        self.total_lines = scan_result.total_size
        
        # 遍历所有文件结果
        for result in file_results:
            self._aggregate_file(result)
        
        # 计算平均值
        avg_complexity = self.total_complexity / max(1, self.file_count)
        avg_maintainability = self.total_maintainability / max(1, self.file_count)
        
        # 找出最大复杂度的文件
        max_complexity_file = None
        max_complexity_value = 0
        for file_path, complexity in self.complexity_by_file.items():
            if complexity > max_complexity_value:
                max_complexity_value = complexity
                max_complexity_file = file_path
        
        # 统计全局问题
        circular_count = sum(1 for issue in global_issues 
                           if issue.issue_type == 'circular_dependency')
        unused_count = sum(1 for issue in global_issues 
                         if issue.issue_type == 'unused_export')
        
        # 估算测试覆盖率
        test_files = sum(1 for f in scan_result.file_infos if f.is_test)
        test_coverage = (test_files / max(1, self.total_files)) * 100
        
        return ProjectMetrics(
            total_files=self.total_files,
            total_lines=self.total_lines,
            total_functions=self.total_functions,
            total_classes=self.total_classes,
            avg_complexity=round(avg_complexity, 2),
            avg_maintainability=round(avg_maintainability, 2),
            max_complexity_file=max_complexity_file,
            max_complexity_value=max_complexity_value,
            dependency_count=self._count_dependencies(scan_result),
            circular_dependency_count=circular_count,
            unused_export_count=unused_count,
            test_coverage_estimate=round(test_coverage, 2),
        )
    
    def _aggregate_file(self, result: FileAnalysisResult) -> None:
        """聚合单个文件的结果"""
        summary = result.summary
        
        self.total_lines += summary.lines_of_code
        self.total_functions += summary.function_count
        self.total_classes += summary.class_count
        self.total_complexity += summary.cyclomatic_complexity
        self.total_maintainability += summary.maintainability_index
        
        self.complexity_by_file[result.file.relative_path] = summary.cyclomatic_complexity
        self.file_count += 1
    
    def _count_dependencies(self, scan_result: ProjectScanResult) -> int:
        """估算依赖数量"""
        # 简单估算：文件数量 - 1 作为最小依赖图
        return max(0, scan_result.total_files - 1)
    
    def get_quality_score(self, metrics: ProjectMetrics) -> float:
        """
        计算项目整体质量分数（0-100）
        
        考虑因素：
        - 平均复杂度（越低越好）
        - 平均可维护性（越高越好）
        - 循环依赖（越少越好）
        - 未使用导出（越少越好）
        """
        score = 100.0
        
        # 复杂度惩罚（每超过 10 扣 5 分，最多扣 30 分）
        complexity_penalty = min(30, (metrics.avg_complexity - 10) * 5)
        if complexity_penalty > 0:
            score -= complexity_penalty
        
        # 可维护性加分（每增加 10 加 3 分）
        maintainability_bonus = (metrics.avg_maintainability / 10) * 3
        score += min(20, maintainability_bonus)
        
        # 循环依赖惩罚（每个扣 5 分，最多扣 25 分）
        circular_penalty = min(25, metrics.circular_dependency_count * 5)
        score -= circular_penalty
        
        # 未使用导出惩罚（每个扣 1 分，最多扣 10 分）
        unused_penalty = min(10, metrics.unused_export_count)
        score -= unused_penalty
        
        # 测试覆盖率加分（每 10% 加 2 分，最多加 20 分）
        test_bonus = min(20, (metrics.test_coverage_estimate / 10) * 2)
        score += test_bonus
        
        return max(0, min(100, round(score, 1)))
    
    def get_risk_assessment(self, metrics: ProjectMetrics) -> Dict[str, Any]:
        """
        获取风险评估
        
        Returns:
            风险评估结果
        """
        risks = []
        
        # 高复杂度风险
        if metrics.avg_complexity > 15:
            risks.append({
                'type': 'high_complexity',
                'severity': 'high' if metrics.avg_complexity > 20 else 'medium',
                'message': f"平均圈复杂度较高 ({metrics.avg_complexity})",
                'recommendation': '考虑重构复杂的函数，拆分为更小的单元',
            })
        
        # 循环依赖风险
        if metrics.circular_dependency_count > 0:
            risks.append({
                'type': 'circular_dependency',
                'severity': 'high' if metrics.circular_dependency_count > 3 else 'medium',
                'message': f"存在 {metrics.circular_dependency_count} 个循环依赖",
                'recommendation': '重构模块结构，引入中间层打破循环',
            })
        
        # 可维护性风险
        if metrics.avg_maintainability < 50:
            risks.append({
                'type': 'low_maintainability',
                'severity': 'high' if metrics.avg_maintainability < 30 else 'medium',
                'message': f"平均可维护性指数较低 ({metrics.avg_maintainability})",
                'recommendation': '减少代码嵌套，提高模块化程度',
            })
        
        # 测试覆盖风险
        if metrics.test_coverage_estimate < 20:
            risks.append({
                'type': 'low_test_coverage',
                'severity': 'medium',
                'message': f"测试覆盖率估算较低 ({metrics.test_coverage_estimate}%)",
                'recommendation': '添加单元测试以提高代码质量',
            })
        
        # 最大复杂度文件风险
        if metrics.max_complexity_value > 30:
            risks.append({
                'type': 'complex_file',
                'severity': 'high',
                'message': f"文件 '{metrics.max_complexity_file}' 复杂度过高 ({metrics.max_complexity_value})",
                'recommendation': '优先重构此文件，拆分职责',
            })
        
        return {
            'risk_count': len(risks),
            'high_risk_count': sum(1 for r in risks if r['severity'] == 'high'),
            'risks': risks,
        }
    
    def get_summary_text(self, metrics: ProjectMetrics) -> str:
        """生成项目摘要文本"""
        quality_score = self.get_quality_score(metrics)
        risk = self.get_risk_assessment(metrics)
        
        lines = [
            f"项目包含 {metrics.total_files} 个 Python 文件，共 {metrics.total_lines} 行代码。",
            f"定义了 {metrics.total_functions} 个函数和 {metrics.total_classes} 个类。",
            f"平均圈复杂度: {metrics.avg_complexity}，平均可维护性指数: {metrics.avg_maintainability}。",
            f"整体质量评分: {quality_score}/100",
        ]
        
        if risk['high_risk_count'] > 0:
            lines.append(f"发现 {risk['high_risk_count']} 个高风险问题需要关注。")
        
        if metrics.circular_dependency_count > 0:
            lines.append(f"存在 {metrics.circular_dependency_count} 个循环依赖需要解决。")
        
        return '\n'.join(lines)
