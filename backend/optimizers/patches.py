"""
Patch Generator - 代码补丁生成器
生成可自动应用的代码修复补丁
"""
import ast
import difflib
import re
from typing import List, Dict, Any, Optional, Tuple
from ..models.schemas import OptimizationSuggestion


class PatchGenerator:
    """代码补丁生成器"""
    
    def __init__(self):
        self.patches: List[Dict[str, Any]] = []
    
    def generate_patch(
        self, 
        original_code: str, 
        suggestion: OptimizationSuggestion
    ) -> Optional[str]:
        """
        生成统一差异格式的补丁
        
        Args:
            original_code: 原始代码
            suggestion: 优化建议
        
        Returns:
            统一差异格式的补丁字符串
        """
        if not suggestion.auto_fixable:
            return None
        
        # 尝试应用修复
        fixed_code = self._apply_fix(original_code, suggestion)
        
        if fixed_code is None or fixed_code == original_code:
            return None
        
        # 生成差异
        diff = self._generate_unified_diff(
            original_code, 
            fixed_code, 
            fromfile='original',
            tofile='fixed'
        )
        
        return diff
    
    def _apply_fix(self, code: str, suggestion: OptimizationSuggestion) -> Optional[str]:
        """应用具体的修复"""
        lines = code.splitlines()
        
        # 根据建议类型应用不同的修复策略
        if suggestion.category == 'performance':
            return self._apply_performance_fix(code, suggestion)
        elif suggestion.category == 'readability':
            return self._apply_readability_fix(code, suggestion)
        elif suggestion.category == 'security':
            return self._apply_security_fix(code, suggestion)
        
        return None
    
    def _apply_performance_fix(self, code: str, suggestion: OptimizationSuggestion) -> Optional[str]:
        """应用性能优化修复"""
        
        # 列表推导式转生成器表达式
        if '生成器' in suggestion.title:
            # 找到函数参数中的列表推导式
            pattern = r'(\w+)\(([\[].*?[\]])\)'
            
            def replace_listcomp_with_gen(match):
                func_name = match.group(1)
                listcomp = match.group(2)
                if listcomp.startswith('[') and listcomp.endswith(']'):
                    genexpr = '(' + listcomp[1:-1] + ')'
                    return f'{func_name}({genexpr})'
                return match.group(0)
            
            result = re.sub(pattern, replace_listcomp_with_gen, code, flags=re.DOTALL)
            return result if result != code else None
        
        # 字符串拼接优化
        if '字符串拼接' in suggestion.title or 'join' in suggestion.title:
            return self._fix_string_concat(code)
        
        # 集合优化
        if '集合' in suggestion.title and '成员检查' in suggestion.title:
            return self._fix_list_membership(code)
        
        return None
    
    def _apply_readability_fix(self, code: str, suggestion: OptimizationSuggestion) -> Optional[str]:
        """应用可读性修复"""
        
        # range(len()) -> enumerate()
        if 'enumerate' in suggestion.title.lower():
            return self._fix_range_len(code)
        
        # 格式化字符串 -> f-string
        if 'f-string' in suggestion.title.lower():
            return self._fix_format_string(code)
        
        return None
    
    def _apply_security_fix(self, code: str, suggestion: OptimizationSuggestion) -> Optional[str]:
        """应用安全修复"""
        
        # eval -> ast.literal_eval
        if 'eval' in suggestion.title.lower() or 'literal_eval' in suggestion.title.lower():
            # 简单替换
            result = re.sub(
                r'\beval\s*\(',
                'ast.literal_eval(',
                code
            )
            # 确保导入了ast
            if 'ast.literal_eval' in result and 'import ast' not in result:
                result = 'import ast\n' + result
            return result if result != code else None
        
        return None
    
    def _fix_string_concat(self, code: str) -> Optional[str]:
        """修复循环中的字符串拼接"""
        lines = code.splitlines()
        result_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # 检测 += 字符串拼接模式
            if '+=' in line and '"' in line or "'" in line:
                # 提取变量名
                match = re.match(r'\s*(\w+)\s*\+=\s*(.+)', line)
                if match:
                    var_name = match.group(1)
                    value = match.group(2).strip()
                    
                    # 检查是否在循环内（简化判断）
                    indent = len(line) - len(line.lstrip())
                    
                    # 生成修复代码
                    result_lines.append(' ' * indent + f'{var_name}_parts.append({value})')
                else:
                    result_lines.append(line)
            else:
                result_lines.append(line)
            
            i += 1
        
        result = '\n'.join(result_lines)
        return result if result != code else None
    
    def _fix_list_membership(self, code: str) -> Optional[str]:
        """修复列表成员检查"""
        lines = code.splitlines()
        result_lines = []
        conversions = {}
        
        for line in lines:
            # 查找 if x in list: 模式
            match = re.search(r'if\s+(\w+)\s+in\s+(\w+)\s*:', line)
            if match:
                item, lst = match.groups()
                if lst in conversions:
                    # 已经转换过
                    new_line = line.replace(f'in {lst}', f'in {conversions[lst]}')
                    result_lines.append(new_line)
                else:
                    # 需要转换
                    set_name = f'{lst}_set'
                    conversions[lst] = set_name
                    result_lines.append(f'{set_name} = set({lst})')
                    new_line = line.replace(f'in {lst}', f'in {set_name}')
                    result_lines.append(new_line)
            else:
                result_lines.append(line)
        
        result = '\n'.join(result_lines)
        return result if result != code else None
    
    def _fix_range_len(self, code: str) -> Optional[str]:
        """修复 range(len()) 模式"""
        lines = code.splitlines()
        result_lines = []
        
        for line in lines:
            # 匹配 for i in range(len(seq)):
            match = re.match(
                r'(\s*)for\s+(\w+)\s+in\s+range\(len\((\w+)\)\)\s*:',
                line
            )
            if match:
                indent, index_var, seq_name = match.groups()
                new_line = f'{indent}for {index_var}, item in enumerate({seq_name}):'
                result_lines.append(new_line)
            else:
                result_lines.append(line)
        
        result = '\n'.join(result_lines)
        return result if result != code else None
    
    def _fix_format_string(self, code: str) -> Optional[str]:
        """将格式化字符串转换为f-string"""
        result = code
        
        # % 格式化 -> f-string
        # 简化实现：处理简单情况
        pattern = r'(["\'])([^"\']*%[sd])\1\s*%\s*\(([^)]+)\)'
        
        def convert_percent_format(match):
            quote = match.group(1)
            template = match.group(2)
            args = match.group(3)
            
            # 将 %s 和 %d 替换为 {var}
            vars_list = [v.strip() for v in args.split(',')]
            fstring = template
            
            for var in vars_list:
                fstring = fstring.replace('%s', '{' + var + '}', 1)
                fstring = fstring.replace('%d', '{' + var + '}', 1)
            
            return 'f' + quote + fstring + quote
        
        result = re.sub(pattern, convert_percent_format, result)
        
        return result if result != code else None
    
    def _generate_unified_diff(
        self, 
        original: str, 
        modified: str,
        fromfile: str = 'original',
        tofile: str = 'modified'
    ) -> str:
        """生成统一差异格式"""
        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=fromfile,
            tofile=tofile,
            lineterm=''
        )
        
        return ''.join(diff)
    
    def apply_patch(self, code: str, patch: str) -> Optional[str]:
        """
        应用补丁到代码
        
        Args:
            code: 原始代码
            patch: 统一差异格式的补丁
        
        Returns:
            修复后的代码，失败返回None
        """
        lines = code.splitlines()
        patch_lines = patch.splitlines()
        
        # 解析补丁
        hunks = self._parse_patch_hunks(patch_lines)
        
        # 应用每个hunk
        offset = 0
        for hunk in hunks:
            start_line = hunk['start_line'] - 1 + offset
            deleted_count = hunk['deleted']
            new_lines = hunk['lines']
            
            # 替换行
            lines[start_line:start_line + deleted_count] = new_lines
            offset += len(new_lines) - deleted_count
        
        return '\n'.join(lines)
    
    def _parse_patch_hunks(self, patch_lines: List[str]) -> List[Dict[str, Any]]:
        """解析补丁中的hunks"""
        hunks = []
        current_hunk = None
        
        for line in patch_lines:
            if line.startswith('@@'):
                # 新hunk开始
                if current_hunk:
                    hunks.append(current_hunk)
                
                # 解析 @@ -start,count +start,count @@
                match = re.match(r'@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@', line)
                if match:
                    current_hunk = {
                        'start_line': int(match.group(2)),
                        'deleted': 0,
                        'lines': []
                    }
            elif current_hunk is not None:
                if line.startswith('+') and not line.startswith('+++'):
                    # 新增行
                    current_hunk['lines'].append(line[1:])
                elif line.startswith('-') and not line.startswith('---'):
                    # 删除行
                    current_hunk['deleted'] += 1
                elif not line.startswith('\\'):
                    # 上下文行
                    current_hunk['lines'].append(line[1:] if line else '')
        
        if current_hunk:
            hunks.append(current_hunk)
        
        return hunks
    
    def generate_all_patches(
        self, 
        code: str, 
        suggestions: List[OptimizationSuggestion]
    ) -> List[Dict[str, Any]]:
        """
        为所有可自动修复的建议生成补丁
        
        Args:
            code: 原始代码
            suggestions: 优化建议列表
        
        Returns:
            补丁信息列表
        """
        self.patches = []
        
        for suggestion in suggestions:
            patch = self.generate_patch(code, suggestion)
            if patch:
                self.patches.append({
                    'suggestion_id': suggestion.id,
                    'category': suggestion.category,
                    'title': suggestion.title,
                    'patch': patch
                })
        
        return self.patches
