"""
Circular Dependency Detector - 检测循环依赖
"""
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict
from dataclasses import dataclass

from .models import GlobalIssue
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CycleInfo:
    """循环依赖信息"""
    modules: List[str]
    length: int
    severity: str  # 'critical', 'warning', 'info'


class CycleDetector:
    """循环依赖检测器"""
    
    def __init__(self, dependency_graph: Dict[str, List[str]]):
        """
        初始化检测器
        
        Args:
            dependency_graph: 依赖图 {module: [dependencies]}
        """
        self.graph = dependency_graph
        self.adjacency = defaultdict(set)
        
        # 构建邻接表
        for module, deps in dependency_graph.items():
            for dep in deps:
                self.adjacency[module].add(dep)
    
    def detect(self) -> List[GlobalIssue]:
        """
        检测所有循环依赖
        
        Returns:
            循环依赖问题列表
        """
        cycles = self._find_all_cycles()
        issues = []
        
        seen_cycles = set()  # 用于去重
        
        for cycle in cycles:
            # 标准化循环（从最小元素开始）
            normalized = self._normalize_cycle(cycle)
            cycle_key = tuple(normalized)
            
            if cycle_key in seen_cycles:
                continue
            seen_cycles.add(cycle_key)
            
            # 确定严重程度
            severity = self._get_severity(normalized)
            
            issue = GlobalIssue(
                issue_type='circular_dependency',
                severity=severity,
                message=self._generate_message(normalized),
                locations=[
                    {
                        'file_path': module,
                        'type': 'module',
                    }
                    for module in normalized
                ],
                suggestion=self._generate_suggestion(normalized),
            )
            issues.append(issue)
        
        if issues:
            logger.warning(f"检测到 {len(issues)} 个循环依赖")
        
        return issues
    
    def _find_all_cycles(self) -> List[List[str]]:
        """使用迭代式 DFS 查找所有循环（避免递归栈溢出）"""
        cycles = []
        visited = set()
        
        # 使用显式栈进行迭代式 DFS
        # 栈元素: (node, path, rec_stack_set)
        for start_node in list(self.adjacency.keys()):
            if start_node in visited:
                continue
            
            # 每个起始节点的独立 DFS
            stack = [(start_node, [], set())]
            
            while stack:
                node, path, rec_stack = stack.pop()
                
                if node in rec_stack:
                    # 找到循环：从循环起点到当前节点
                    cycle_start = path.index(node) if node in path else -1
                    if cycle_start >= 0:
                        cycle = path[cycle_start:] + [node]
                        cycles.append(cycle)
                    continue
                
                if node in visited and node not in rec_stack:
                    # 已访问过且不在当前递归栈中，跳过
                    continue
                
                # 标记访问
                new_path = path + [node]
                new_rec_stack = rec_stack | {node}
                visited.add(node)
                
                # 遍历邻居（逆序以保持原有顺序）
                neighbors = list(self.adjacency.get(node, []))
                for neighbor in reversed(neighbors):
                    if neighbor in new_rec_stack:
                        # 找到循环
                        cycle_start = new_path.index(neighbor) if neighbor in new_path else -1
                        if cycle_start >= 0:
                            cycle = new_path[cycle_start:] + [neighbor]
                            cycles.append(cycle)
                    else:
                        stack.append((neighbor, new_path, new_rec_stack))
        
        return cycles
    
    def _normalize_cycle(self, cycle: List[str]) -> List[str]:
        """
        标准化循环表示
        从最小的模块名开始，保持循环方向
        """
        if len(cycle) <= 1:
            return cycle
        
        # 移除重复的末尾元素
        if cycle[0] == cycle[-1]:
            cycle = cycle[:-1]
        
        if not cycle:
            return cycle
        
        # 找到最小元素的位置
        min_idx = cycle.index(min(cycle))
        
        # 旋转使最小元素在开头
        normalized = cycle[min_idx:] + cycle[:min_idx]
        
        return normalized
    
    def _get_severity(self, cycle: List[str]) -> str:
        """
        确定循环依赖的严重程度
        
        规则：
        - 2 个模块的直接循环: critical
        - 3-4 个模块: warning
        - 5+ 个模块: info
        """
        length = len(cycle)
        
        if length <= 2:
            return 'critical'
        elif length <= 4:
            return 'warning'
        else:
            return 'info'
    
    def _generate_message(self, cycle: List[str]) -> str:
        """生成问题描述"""
        if len(cycle) <= 2:
            return f"直接循环依赖: {' <-> '.join(cycle)}"
        else:
            return f"循环依赖链 ({len(cycle)} 个模块): {' -> '.join(cycle)} -> {cycle[0]}"
    
    def _generate_suggestion(self, cycle: List[str]) -> str:
        """生成修复建议"""
        if len(cycle) <= 2:
            return (
                "建议重构以打破循环：\n"
                "1. 将共享逻辑提取到独立的公共模块\n"
                "2. 使用依赖注入代替直接导入\n"
                "3. 考虑使用接口/抽象基类"
            )
        else:
            return (
                "建议简化模块结构：\n"
                "1. 检查依赖链中的每个环节是否必要\n"
                "2. 考虑引入中间模块解耦\n"
                "3. 使用延迟导入"
            )
    
    def get_strongly_connected_components(self) -> List[Set[str]]:
        """
        使用迭代式 Tarjan 算法查找强连通分量
        
        Returns:
            强连通分量列表
        """
        index_counter = [0]
        stack = []
        lowlinks = {}
        index = {}
        on_stack = {}
        sccs = []
        
        # 使用显式栈进行迭代式处理
        # 栈元素: (node, 'enter'|'exit', neighbors_iterator)
        for node in list(self.adjacency.keys()):
            if node in index:
                continue
            
            process_stack = [(node, 'enter', None)]
            
            while process_stack:
                current, state, neighbors_iter = process_stack.pop()
                
                if state == 'enter':
                    # 首次访问节点
                    index[current] = index_counter[0]
                    lowlinks[current] = index_counter[0]
                    index_counter[0] += 1
                    stack.append(current)
                    on_stack[current] = True
                    
                    # 创建邻居迭代器
                    neighbor_list = list(self.adjacency.get(current, []))
                    process_stack.append((current, 'exit', iter(neighbor_list)))
                    
                elif state == 'exit':
                    # 处理邻居
                    try:
                        successor = next(neighbors_iter)
                        if successor not in index:
                            # 后继未访问，先访问后继
                            process_stack.append((current, 'exit', neighbors_iter))
                            process_stack.append((successor, 'enter', None))
                        elif on_stack.get(successor, False):
                            lowlinks[current] = min(lowlinks[current], index[successor])
                        else:
                            # 继续下一个邻居
                            process_stack.append((current, 'exit', neighbors_iter))
                    except StopIteration:
                        # 所有邻居处理完毕，检查是否是 SCC 根
                        if lowlinks[current] == index[current]:
                            scc = set()
                            while True:
                                successor = stack.pop()
                                on_stack[successor] = False
                                scc.add(successor)
                                if successor == current:
                                    break
                            if len(scc) > 1:
                                sccs.append(scc)
        
        return sccs
