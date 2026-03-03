"""
Unused Export Detector - 检测未被使用的导出符号
"""
import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
from dataclasses import dataclass

from .models import GlobalIssue
from .symbol_extractor import SymbolExtractor, SymbolDefinition, SymbolUsage
from .dependency import DependencyAnalyzer
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class UnusedSymbol:
    """未使用的符号"""
    name: str
    module: str
    type: str
    lineno: int
    is_exported: bool


class UnusedExportDetector:
    """未使用导出检测器"""
    
    # 常见的隐式使用入口点
    ENTRY_POINTS = {
        'main',
        '__main__',
        'setup',
        'pytest_configure',
        'pytest_collection_modifyitems',
        'app',
        'create_app',
        'get_app',
    }
    
    # 特殊方法（通常不会直接调用）
    MAGIC_METHODS = {
        '__init__', '__new__', '__del__',
        '__repr__', '__str__', '__format__',
        '__bytes__', '__bool__', '__len__',
        '__iter__', '__next__', '__reversed__',
        '__getitem__', '__setitem__', '__delitem__',
        '__contains__', '__call__', '__enter__',
        '__exit__', '__getattr__', '__setattr__',
        '__delattr__', '__eq__', '__ne__',
        '__lt__', '__le__', '__gt__', '__ge__',
        '__hash__', '__add__', '__sub__',
        '__mul__', '__truediv__', '__floordiv__',
        '__mod__', '__pow__', '__and__',
        '__or__', '__xor__', '__radd__',
        '__rsub__', '__rmul__', '__rtruediv__',
        '__rfloordiv__', '__rmod__', '__rpow__',
        '__rand__', '__ror__', '__rxor__',
        '__iadd__', '__isub__', '__imul__',
        '__itruediv__', '__ifloordiv__',
        '__imod__', '__ipow__', '__iand__',
        '__ior__', '__ixor__', '__neg__',
        '__pos__', '__abs__', '__invert__',
        '__complex__', '__int__', '__float__',
        '__index__', '__round__', '__trunc__',
        '__floor__', '__ceil__',
    }
    
    def __init__(self, dependency_analyzer: DependencyAnalyzer):
        """
        初始化检测器
        
        Args:
            dependency_analyzer: 依赖分析器
        """
        self.dependency_analyzer = dependency_analyzer
        self.symbol_extractor = SymbolExtractor()
        
        # 内部状态
        self.exported_symbols: Dict[str, List[SymbolDefinition]] = {}
        self.used_symbols: Dict[str, Set[str]] = defaultdict(set)
    
    def detect(self, module_files: Dict[str, str]) -> List[GlobalIssue]:
        """
        检测未使用的导出符号
        
        Args:
            module_files: {module_name: file_path}
        
        Returns:
            未使用导出问题列表
        """
        # 提取所有符号定义和使用
        definitions, usages = self.symbol_extractor.extract_from_project(module_files)
        
        # 构建模块到文件的映射
        self._build_usage_map(usages, module_files)
        
        issues = []
        
        for module_name, defs in definitions.items():
            for definition in defs:
                # 只检查公开符号
                if not definition.is_public:
                    continue
                
                # 跳过特殊方法
                if definition.name in self.MAGIC_METHODS:
                    continue
                
                # 跳过入口点
                if definition.name in self.ENTRY_POINTS:
                    continue
                
                # 检查是否被使用
                if self._is_symbol_used(definition, module_name, module_files):
                    continue
                
                # 找到未使用的符号
                issue = GlobalIssue(
                    issue_type='unused_export',
                    severity='info',
                    message=f"符号 '{definition.name}' 已导出但未被项目内其他模块使用",
                    locations=[
                        {
                            'file_path': module_name,
                            'lineno': definition.lineno,
                            'symbol': definition.name,
                            'type': definition.type,
                        }
                    ],
                    suggestion=self._generate_suggestion(definition),
                )
                issues.append(issue)
        
        if issues:
            logger.info(f"检测到 {len(issues)} 个可能未使用的导出符号")
        
        return issues
    
    def _build_usage_map(self, usages: Dict[str, List[SymbolUsage]], 
                         module_files: Dict[str, str]) -> None:
        """构建符号使用映射"""
        for symbol_name, usage_list in usages.items():
            for usage in usage_list:
                # 尝试解析符号来源
                source_module = usage.source_module
                
                # 获取该模块的依赖
                deps = self.dependency_analyzer.get_dependencies(source_module)
                
                # 记录使用
                self.used_symbols[symbol_name].add(source_module)
                
                # 如果有来源模块信息，也记录
                if usage.module:
                    self.used_symbols[symbol_name].add(usage.module)
    
    def _is_symbol_used(self, definition: SymbolDefinition, module_name: str,
                        module_files: Dict[str, str]) -> bool:
        """
        检查符号是否被使用
        
        Args:
            definition: 符号定义
            module_name: 定义所在的模块
            module_files: 模块文件映射
        
        Returns:
            是否被使用
        """
        symbol_name = definition.name
        
        # 检查是否在 __all__ 中
        exports = self.symbol_extractor.module_exports.get(module_name, set())
        if symbol_name in exports:
            # 在 __all__ 中，可能是公共 API，不报告
            return True
        
        # 获取依赖此模块的其他模块
        dependents = self.dependency_analyzer.get_dependents(module_name)
        
        if not dependents:
            # 没有模块依赖此模块，检查是否是入口点
            return self._is_entry_module(module_name, module_files)
        
        # 检查是否在依赖模块中被使用
        for dependent in dependents:
            if symbol_name in self.used_symbols:
                # 检查使用是否来自依赖模块
                usages = self.used_symbols[symbol_name]
                if dependent in usages:
                    return True
        
        # 检查模块内部使用
        return self._is_used_internally(definition, module_name, module_files)
    
    def _is_entry_module(self, module_name: str, module_files: Dict[str, str]) -> bool:
        """检查是否是入口模块"""
        # __main__.py 或包含 main() 函数的模块
        if '__main__' in module_name:
            return True
        
        file_path = module_files.get(module_name)
        if file_path:
            try:
                content = Path(file_path).read_text(encoding='utf-8', errors='ignore')
                tree = ast.parse(content)
                
                for node in ast.iter_child_nodes(tree):
                    if isinstance(node, ast.FunctionDef) and node.name == 'main':
                        return True
                    if isinstance(node, ast.If):
                        # 检查 if __name__ == '__main__':
                        if self._is_main_block(node):
                            return True
            except Exception:
                pass
        
        return False
    
    def _is_main_block(self, node: ast.If) -> bool:
        """检查是否是 if __name__ == '__main__' 块"""
        test = node.test
        if isinstance(test, ast.Compare):
            if len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq):
                if isinstance(test.left, ast.Name) and test.left.id == '__name__':
                    if test.comparators and isinstance(test.comparators[0], ast.Constant):
                        return test.comparators[0].value == '__main__'
        return False
    
    def _is_used_internally(self, definition: SymbolDefinition, module_name: str,
                           module_files: Dict[str, str]) -> bool:
        """检查符号是否在模块内部被使用"""
        file_path = module_files.get(module_name)
        if not file_path:
            return False
        
        try:
            content = Path(file_path).read_text(encoding='utf-8', errors='ignore')
            tree = ast.parse(content)
            
            # 查找符号的所有使用
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and node.id == definition.name:
                    # 检查是否是使用（而非定义）
                    if isinstance(node.ctx, ast.Load):
                        # 检查行号是否在定义之后
                        if node.lineno > definition.lineno:
                            return True
            
            return False
        except Exception:
            return False
    
    def _generate_suggestion(self, definition: SymbolDefinition) -> str:
        """生成修复建议"""
        suggestions = []
        
        if definition.type == 'function':
            suggestions.append("如果此函数是公共 API，考虑在 __all__ 中显式声明")
            suggestions.append("如果此函数不再需要，可以删除或标记为私有（添加下划线前缀）")
        elif definition.type == 'class':
            suggestions.append("如果此类是公共 API，考虑在 __all__ 中显式声明")
            suggestions.append("如果此类是内部实现，考虑添加下划线前缀")
        else:
            suggestions.append("考虑将此符号添加到 __all__ 或标记为私有")
        
        return '\n'.join(suggestions)
