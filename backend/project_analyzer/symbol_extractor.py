"""
Symbol Extractor - 提取模块中的符号定义和使用
"""
import ast
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SymbolDefinition:
    """符号定义"""
    name: str
    type: str  # 'function', 'class', 'variable', 'constant', 'import'
    module: str
    lineno: int
    col_offset: int = 0
    is_public: bool = True
    is_exported: bool = False  # 是否在 __all__ 中


@dataclass
class SymbolUsage:
    """符号使用"""
    name: str
    module: str
    source_module: str  # 使用该符号的模块
    lineno: int
    context: str = ''  # 使用上下文


class SymbolExtractor:
    """符号提取器"""
    
    def __init__(self):
        self.definitions: Dict[str, List[SymbolDefinition]] = defaultdict(list)
        self.usages: Dict[str, List[SymbolUsage]] = defaultdict(list)
        self.module_exports: Dict[str, Set[str]] = {}  # module -> __all__ 内容
    
    def extract_from_project(self, module_files: Dict[str, str]) -> Tuple[Dict[str, List[SymbolDefinition]], Dict[str, List[SymbolUsage]]]:
        """
        从项目中提取所有符号
        
        Args:
            module_files: {module_name: file_path}
        
        Returns:
            (定义字典, 使用字典)
        """
        # 第一遍：提取所有定义
        for module_name, file_path in module_files.items():
            self._extract_definitions(module_name, file_path)
        
        # 第二遍：提取所有使用
        for module_name, file_path in module_files.items():
            self._extract_usages(module_name, file_path)
        
        return dict(self.definitions), dict(self.usages)
    
    def _extract_definitions(self, module_name: str, file_path: str) -> None:
        """提取模块中的符号定义"""
        try:
            content = Path(file_path).read_text(encoding='utf-8', errors='ignore')
            tree = ast.parse(content)
        except (SyntaxError, UnicodeDecodeError) as e:
            logger.warning(f"解析文件失败: {file_path}: {e}")
            return
        
        # 检查 __all__
        exports = self._extract_all(tree)
        self.module_exports[module_name] = exports
        
        # 提取顶层定义
        for node in ast.iter_child_nodes(tree):
            definition = self._node_to_definition(node, module_name)
            if definition:
                # 检查是否公开
                definition.is_public = not definition.name.startswith('_')
                definition.is_exported = definition.name in exports if exports else definition.is_public
                self.definitions[module_name].append(definition)
    
    def _extract_all(self, tree: ast.AST) -> Set[str]:
        """提取 __all__ 内容"""
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == '__all__':
                        if isinstance(node.value, ast.List):
                            exports = set()
                            for elt in node.value.elts:
                                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                    exports.add(elt.value)
                            return exports
        return set()
    
    def _node_to_definition(self, node: ast.AST, module_name: str) -> Optional[SymbolDefinition]:
        """将 AST 节点转换为符号定义"""
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            return SymbolDefinition(
                name=node.name,
                type='function',
                module=module_name,
                lineno=node.lineno,
                col_offset=node.col_offset,
            )
        
        elif isinstance(node, ast.ClassDef):
            return SymbolDefinition(
                name=node.name,
                type='class',
                module=module_name,
                lineno=node.lineno,
                col_offset=node.col_offset,
            )
        
        elif isinstance(node, ast.Assign):
            # 只处理单个目标的简单赋值
            if len(node.targets) == 1:
                target = node.targets[0]
                if isinstance(target, ast.Name):
                    # 判断是否是常量（大写名称）
                    is_constant = target.id.isupper() or (
                        target.id[0].isupper() and '_' in target.id
                    )
                    return SymbolDefinition(
                        name=target.id,
                        type='constant' if is_constant else 'variable',
                        module=module_name,
                        lineno=node.lineno,
                        col_offset=node.col_offset,
                    )
        
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                return SymbolDefinition(
                    name=node.target.id,
                    type='variable',
                    module=module_name,
                    lineno=node.lineno,
                    col_offset=node.col_offset,
                )
        
        return None
    
    def _extract_usages(self, source_module: str, file_path: str) -> None:
        """提取模块中的符号使用"""
        try:
            content = Path(file_path).read_text(encoding='utf-8', errors='ignore')
            tree = ast.parse(content)
        except (SyntaxError, UnicodeDecodeError) as e:
            logger.warning(f"解析文件失败: {file_path}: {e}")
            return
        
        # 使用访问者提取名称使用
        visitor = UsageVisitor(source_module)
        visitor.visit(tree)
        
        for name, usages in visitor.usages.items():
            self.usages[name].extend(usages)
    
    def get_public_symbols(self, module_name: str) -> List[SymbolDefinition]:
        """获取模块的公开符号"""
        return [
            d for d in self.definitions.get(module_name, [])
            if d.is_public
        ]
    
    def get_exported_symbols(self, module_name: str) -> List[SymbolDefinition]:
        """获取模块的导出符号"""
        return [
            d for d in self.definitions.get(module_name, [])
            if d.is_exported
        ]


class UsageVisitor(ast.NodeVisitor):
    """符号使用访问者"""
    
    def __init__(self, source_module: str):
        self.source_module = source_module
        self.usages: Dict[str, List[SymbolUsage]] = defaultdict(list)
        self._in_definition = False
        self._definition_names: Set[str] = set()
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._definition_names.add(node.name)
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._definition_names.add(node.name)
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._definition_names.add(node.name)
        self.generic_visit(node)
    
    def visit_Name(self, node: ast.Name) -> None:
        # 只记录使用（读取），不记录定义
        if isinstance(node.ctx, ast.Load):
            # 排除局部定义的名称
            if node.id not in self._definition_names:
                self.usages[node.id].append(SymbolUsage(
                    name=node.id,
                    module='',  # 需要后续解析
                    source_module=self.source_module,
                    lineno=node.lineno,
                    context='load',
                ))
        self.generic_visit(node)
    
    def visit_Attribute(self, node: ast.Attribute) -> None:
        # 记录属性访问
        if isinstance(node.ctx, ast.Load):
            self.usages[node.attr].append(SymbolUsage(
                name=node.attr,
                module='',  # 需要后续解析
                source_module=self.source_module,
                lineno=node.lineno,
                context='attribute',
            ))
        self.generic_visit(node)
