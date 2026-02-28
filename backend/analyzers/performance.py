"""
Performance Analyzer - 性能热点检测
识别嵌套循环、递归、低效操作等
"""
import ast
from typing import List, Dict, Any, Optional, Set
from ..models.schemas import PerformanceHotspot, CodeIssue, SeverityLevel


class PerformanceAnalyzer:
    """性能热点分析器"""
    
    # 不推荐的操作及其替代方案
    INEFFICIENT_PATTERNS = {
        # 字符串拼接
        "string_concat_in_loop": {
            "message": "在循环中使用字符串拼接，应使用列表join",
            "suggestion": "使用 list.append() + ''.join() 替代字符串拼接",
        },
        # 列表操作
        "list_insert_at_start": {
            "message": "在列表开头插入元素，时间复杂度O(n)",
            "suggestion": "考虑使用 collections.deque 或在列表末尾添加后反转",
        },
        # 字典操作
        "dict_key_in_list": {
            "message": "使用list进行成员检查，应使用set",
            "suggestion": "将列表转换为集合进行成员检查，时间复杂度从O(n)降至O(1)",
        },
        # 重复计算
        "repeated_calculation": {
            "message": "检测到可能重复计算的表达式",
            "suggestion": "将不变的计算提取到循环外",
        },
    }
    
    def __init__(self):
        self.hotspots: List[PerformanceHotspot] = []
        self.issues: List[CodeIssue] = []
        self.hotspot_counter = 0
    
    def _generate_hotspot_id(self) -> str:
        self.hotspot_counter += 1
        return f"hotspot_{self.hotspot_counter}"
    
    def analyze(self, code: str, tree: Optional[ast.AST] = None) -> List[PerformanceHotspot]:
        """
        分析代码性能热点
        
        Args:
            code: 源代码字符串
            tree: 可选的AST树
        
        Returns:
            性能热点列表
        """
        if tree is None:
            tree = ast.parse(code)
        
        self.hotspots = []
        self.issues = []
        self.hotspot_counter = 0
        
        # 执行各项检测
        self._detect_nested_loops(tree)
        self._detect_recursion(tree)
        self._detect_inefficient_operations(tree)
        self._detect_large_data_operations(tree)
        self._detect_global_lookups(tree)
        
        return self.hotspots
    
    def _detect_nested_loops(self, tree: ast.AST):
        """检测嵌套循环"""
        
        class LoopVisitor(ast.NodeVisitor):
            def __init__(self, analyzer):
                self.analyzer = analyzer
                self.loop_stack = []
            
            def visit_For(self, node):
                self._visit_loop(node, "for")
            
            def visit_While(self, node):
                self._visit_loop(node, "while")
            
            def _visit_loop(self, node, loop_type):
                depth = len(self.loop_stack)
                self.loop_stack.append(node)
                
                # 深层嵌套警告
                if depth >= 2:
                    complexity = f"O(n^{depth + 1})"
                    severity = SeverityLevel.ERROR if depth >= 3 else SeverityLevel.WARNING
                    
                    hotspot = PerformanceHotspot(
                        id=self.analyzer._generate_hotspot_id(),
                        node_id="",  # 将在后续关联
                        hotspot_type="nested_loop",
                        description=f"检测到{depth + 1}层嵌套{loop_type}循环，可能导致性能问题",
                        estimated_complexity=complexity,
                        lineno=node.lineno,
                        suggestion=f"考虑使用迭代器、生成器或内置函数如map/filter来减少嵌套层级"
                    )
                    self.analyzer.hotspots.append(hotspot)
                    
                    self.analyzer.issues.append(CodeIssue(
                        id=f"perf_nested_loop_{len(self.analyzer.issues)}",
                        type="performance",
                        severity=severity,
                        message=f"嵌套循环深度: {depth + 1}层，估计复杂度: {complexity}",
                        lineno=node.lineno
                    ))
                
                # 检测循环内的低效操作
                self._check_loop_operations(node)
                
                self.generic_visit(node)
                self.loop_stack.pop()
            
            def _check_loop_operations(self, node):
                """检查循环内的低效操作"""
                for child in ast.walk(node):
                    # 字符串拼接
                    if isinstance(child, ast.AugAssign):
                        if isinstance(child.op, ast.Add):
                            if isinstance(child.target, ast.Name):
                                # 简化检查：在循环内的 += 操作可能是字符串拼接
                                pass
                    
                    # 列表插入开头
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Attribute):
                            if child.func.attr == 'insert' and child.args:
                                if isinstance(child.args[0], ast.Constant) and child.args[0].value == 0:
                                    self.analyzer.issues.append(CodeIssue(
                                        id=f"perf_list_insert_{len(self.analyzer.issues)}",
                                        type="performance",
                                        severity=SeverityLevel.WARNING,
                                        message="在循环内使用list.insert(0, ...)效率低下",
                                        lineno=child.lineno
                                    ))
        
        visitor = LoopVisitor(self)
        visitor.visit(tree)
    
    def _detect_recursion(self, tree: ast.AST):
        """检测递归调用"""
        
        class RecursionVisitor(ast.NodeVisitor):
            def __init__(self, analyzer):
                self.analyzer = analyzer
                self.current_function = None
                self.function_calls = {}
            
            def visit_FunctionDef(self, node):
                old_func = self.current_function
                self.current_function = node.name
                self.function_calls[node.name] = []
                self.generic_visit(node)
                self.current_function = old_func
            
            def visit_Call(self, node):
                if self.current_function:
                    if isinstance(node.func, ast.Name):
                        if node.func.id == self.current_function:
                            # 自递归
                            self.analyzer.hotspots.append(PerformanceHotspot(
                                id=self.analyzer._generate_hotspot_id(),
                                node_id="",
                                hotspot_type="recursion",
                                description=f"函数 '{self.current_function}' 包含递归调用",
                                estimated_complexity="取决于递归深度",
                                lineno=node.lineno,
                                suggestion="确保有明确的终止条件，或考虑使用迭代替代递归以避免栈溢出"
                            ))
                
                self.generic_visit(node)
        
        visitor = RecursionVisitor(self)
        visitor.visit(tree)
    
    def _detect_inefficient_operations(self, tree: ast.AST):
        """检测低效操作"""
        
        for node in ast.walk(tree):
            # 检测 in 操作用于列表
            if isinstance(node, ast.Compare):
                for op in node.ops:
                    if isinstance(op, (ast.In, ast.NotIn)):
                        for comparator in node.comparators:
                            if isinstance(comparator, ast.List):
                                self.issues.append(CodeIssue(
                                    id=f"perf_in_list_{len(self.issues)}",
                                    type="performance",
                                    severity=SeverityLevel.WARNING,
                                    message="对列表使用 'in' 操作效率低下（O(n)），建议使用集合（O(1)）",
                                    lineno=node.lineno,
                                    col_offset=node.col_offset
                                ))
            
            # 检测重复的 len() 调用在循环条件中
            if isinstance(node, ast.For):
                if isinstance(node.iter, ast.Call):
                    if isinstance(node.iter.func, ast.Name) and node.iter.func.id == 'range':
                        for arg in node.iter.args:
                            if isinstance(arg, ast.Call):
                                if isinstance(arg.func, ast.Name) and arg.func.id == 'len':
                                    self.issues.append(CodeIssue(
                                        id=f"perf_len_in_range_{len(self.issues)}",
                                        type="performance",
                                        severity=SeverityLevel.INFO,
                                        message="range(len(...)) 模式，考虑使用 enumerate() 获取更Pythonic的代码",
                                        lineno=node.lineno
                                    ))
            
            # 检测字典的键查找
            if isinstance(node, ast.Subscript):
                if isinstance(node.value, ast.Dict):
                    self.issues.append(CodeIssue(
                        id=f"perf_dict_subscript_{len(self.issues)}",
                        type="performance",
                        severity=SeverityLevel.INFO,
                        message="字典键访问可能引发KeyError，考虑使用dict.get()或处理异常",
                        lineno=node.lineno
                    ))
    
    def _detect_large_data_operations(self, tree: ast.AST):
        """检测大数据量操作"""
        
        for node in ast.walk(tree):
            # 检测列表推导式 vs 生成器表达式
            if isinstance(node, ast.ListComp):
                # 如果只是用于迭代，建议使用生成器
                pass  # 需要上下文判断
            
            # 检测大型字符串格式化
            if isinstance(node, ast.BinOp):
                if isinstance(node.op, ast.Mod) and isinstance(node.right, ast.Tuple):
                    if len(node.right.elts) > 5:
                        self.issues.append(CodeIssue(
                            id=f"perf_string_format_{len(self.issues)}",
                            type="performance",
                            severity=SeverityLevel.INFO,
                            message="多参数字符串格式化，建议使用f-string或.format()方法",
                            lineno=node.lineno
                        ))
    
    def _detect_global_lookups(self, tree: ast.AST):
        """检测可能的全局查找"""
        
        # 检测循环内的全局变量访问
        class GlobalLookupVisitor(ast.NodeVisitor):
            def __init__(self, analyzer):
                self.analyzer = analyzer
                self.in_loop = False
                self.local_vars = set()
            
            def visit_For(self, node):
                old_in_loop = self.in_loop
                self.in_loop = True
                
                # 添加循环变量到局部变量
                if isinstance(node.target, ast.Name):
                    self.local_vars.add(node.target.id)
                
                self.generic_visit(node)
                self.in_loop = old_in_loop
            
            def visit_While(self, node):
                old_in_loop = self.in_loop
                self.in_loop = True
                self.generic_visit(node)
                self.in_loop = old_in_loop
            
            def visit_FunctionDef(self, node):
                # 收集函数局部变量
                old_locals = self.local_vars.copy()
                for arg in node.args.args:
                    self.local_vars.add(arg.arg)
                
                self.generic_visit(node)
                self.local_vars = old_locals
            
            def visit_Name(self, node):
                if self.in_loop and isinstance(node.ctx, ast.Load):
                    if node.id not in self.local_vars:
                        # 可能的全局查找
                        pass  # 需要更多上下文
                self.generic_visit(node)
        
        visitor = GlobalLookupVisitor(self)
        visitor.visit(tree)
    
    def analyze_complexity(self, node: ast.AST) -> str:
        """
        估算代码块的时间复杂度
        返回Big O表示法字符串
        """
        complexity = self._estimate_complexity(node)
        return self._format_complexity(complexity)
    
    def _estimate_complexity(self, node: ast.AST) -> Dict[str, int]:
        """估算复杂度因子"""
        factors = {
            'loops': 0,
            'nested': 0,
            'recursion': False,
            'logarithmic': False,
        }
        
        class ComplexityVisitor(ast.NodeVisitor):
            def __init__(self, factors):
                self.factors = factors
                self.loop_depth = 0
            
            def visit_For(self, node):
                self.factors['loops'] += 1
                self.loop_depth += 1
                self.factors['nested'] = max(self.factors['nested'], self.loop_depth)
                
                # 检测对数复杂度特征
                if isinstance(node.iter, ast.Call):
                    if isinstance(node.iter.func, ast.Name):
                        if node.iter.func.id == 'range':
                            # 检查步长
                            if len(node.iter.args) >= 3:
                                self.factors['logarithmic'] = True
                
                self.generic_visit(node)
                self.loop_depth -= 1
            
            def visit_While(self, node):
                self.factors['loops'] += 1
                self.loop_depth += 1
                self.factors['nested'] = max(self.factors['nested'], self.loop_depth)
                self.generic_visit(node)
                self.loop_depth -= 1
        
        ComplexityVisitor(factors).visit(node)
        return factors
    
    def _format_complexity(self, factors: Dict[str, int]) -> str:
        """格式化复杂度为Big O表示法"""
        nested = factors['nested']
        
        if nested == 0:
            return "O(1)"
        elif nested == 1:
            if factors['logarithmic']:
                return "O(n log n)"
            return "O(n)"
        elif nested == 2:
            return "O(n²)"
        elif nested == 3:
            return "O(n³)"
        else:
            return f"O(n^{nested})"
    
    def get_issues(self) -> List[CodeIssue]:
        """获取问题列表"""
        return self.issues
