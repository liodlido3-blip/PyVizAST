"""
Dependency Analyzer - 分析模块依赖关系
"""
import ast
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

from .models import ImportInfo, DependencyEdge, DependencyGraph
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ModuleInfo:
    """模块信息"""
    path: str
    imports: List[ImportInfo] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    is_package: bool = False


class DependencyAnalyzer:
    """依赖分析器"""
    
    # 标准 library 模块（部分列表）
    STDLIB_MODULES = {
        'os', 'sys', 're', 'json', 'io', 'math', 'random', 'datetime',
        'collections', 'itertools', 'functools', 'typing', 'pathlib',
        'subprocess', 'threading', 'multiprocessing', 'asyncio',
        'logging', 'argparse', 'configparser', 'tempfile', 'shutil',
        'pickle', 'sqlite3', 'http', 'urllib', 'email', 'html', 'xml',
        'unittest', 'doctest', 'pdb', 'profile', 'time', 'copy',
        'abc', 'contextlib', 'dataclasses', 'enum', 'operator',
        'string', 'textwrap', 'unicodedata', 'struct', 'codecs',
        'csv', 'hashlib', 'hmac', 'secrets', 'base64', 'binascii',
        'gzip', 'bz2', 'lzma', 'zipfile', 'tarfile', 'socket',
        'ssl', 'select', 'selectors', 'signal', 'mmap', 'ctypes',
        'warnings', 'traceback', 'exceptions', 'gc', 'inspect',
        'dis', 'ast', 'tokenize', 'keyword', 'token', 'symbol',
        'platform', 'errno', 'stat', 'fileinput', 'glob', 'fnmatch',
        'linecache', 'shutil', 'macpath', 'ntpath', 'posixpath',
        'importlib', 'pkgutil', 'modulefinder', 'runpy', 'zipimport',
        'types', 'weakref', 'builtins', '__future__',
    }
    
    # 常见第三方库
    THIRD_PARTY_MODULES = {
        'numpy', 'pandas', 'matplotlib', 'scipy', 'sklearn', 'tensorflow',
        'torch', 'keras', 'requests', 'flask', 'django', 'fastapi',
        'pydantic', 'sqlalchemy', 'alembic', 'celery', 'redis',
        'pytest', 'selenium', 'beautifulsoup4', 'lxml', 'pillow',
        'cv2', 'opencv', 'pyyaml', 'toml', 'dotenv', 'click',
        'tqdm', 'rich', 'colorama', 'boto3', 'azure', 'google',
        'sentry', 'prometheus', 'celery', 'kombu', 'pika',
        'aiohttp', 'httpx', 'uvicorn', 'gunicorn', 'werkzeug',
        'jinja2', 'mako', 'chameleon', 'markupsafe', 'wtforms',
        'cython', 'numba', 'pypy', 'gevent', 'eventlet',
        'twisted', 'tornado', 'aiofiles', 'aioredis', 'aiomysql',
        'psycopg2', 'pymysql', 'mysql', 'pymongo', 'elasticsearch',
        'cassandra', 'kafka', 'zmq', 'grpc', 'thrift', 'avro',
        'protobuf', 'msgpack', 'snappy', 'zstd', 'lz4',
    }
    
    def __init__(self, project_root: str):
        """
        初始化依赖分析器
        
        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root).resolve()
        self.modules: Dict[str, ModuleInfo] = {}
        self.module_paths: Dict[str, str] = {}  # module_name -> file_path
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
    
    def analyze(self, file_paths: List[str]) -> DependencyGraph:
        """
        分析依赖关系
        
        Args:
            file_paths: 文件路径列表
        
        Returns:
            依赖图
        """
        # 第一遍：收集所有模块信息
        for file_path in file_paths:
            self._analyze_file(file_path)
        
        # 第二遍：构建依赖图
        self._build_dependency_graph()
        
        # 构建返回结果
        nodes = list(self.module_paths.keys())
        edges = []
        
        for source, targets in self.dependency_graph.items():
            for target in targets:
                edges.append({
                    'source': source,
                    'target': target,
                    'type': 'import',
                })
        
        logger.info(f"依赖分析完成: {len(nodes)} 个模块, {len(edges)} 个依赖关系")
        
        return DependencyGraph(
            nodes=nodes,
            edges=edges,
            adjacency_list={k: list(v) for k, v in self.dependency_graph.items()},
        )
    
    def _analyze_file(self, file_path: str) -> None:
        """分析单个文件的导入和导出"""
        path = Path(file_path)
        
        try:
            content = path.read_text(encoding='utf-8', errors='ignore')
            tree = ast.parse(content)
        except (SyntaxError, UnicodeDecodeError) as e:
            logger.warning(f"解析文件失败: {file_path}: {e}")
            return
        
        # 计算模块名
        relative_path = path.relative_to(self.project_root)
        module_name = self._path_to_module_name(relative_path)
        
        # 记录模块路径
        self.module_paths[module_name] = str(relative_path).replace('\\', '/')
        
        # 分析导入
        imports = self._extract_imports(tree)
        
        # 分析导出（顶层定义）
        exports = self._extract_exports(tree)
        
        self.modules[module_name] = ModuleInfo(
            path=str(relative_path).replace('\\', '/'),
            imports=imports,
            exports=exports,
            is_package=path.name == '__init__.py',
        )
    
    def _path_to_module_name(self, relative_path: Path) -> str:
        """将文件路径转换为模块名"""
        parts = list(relative_path.parts)
        
        # 移除 .py 后缀
        if parts and parts[-1].endswith('.py'):
            parts[-1] = parts[-1][:-3]
        
        # 处理 __init__.py
        if parts and parts[-1] == '__init__':
            parts = parts[:-1]
        
        return '.'.join(parts) if parts else '__main__'
    
    def _extract_imports(self, tree: ast.AST) -> List[ImportInfo]:
        """提取导入信息"""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(ImportInfo(
                        module=alias.name,
                        names=[alias.name],
                        alias=alias.asname,
                        is_relative=False,
                        lineno=node.lineno,
                    ))
            
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                is_relative = node.level > 0
                
                names = [alias.name for alias in node.names]
                
                imports.append(ImportInfo(
                    module=module,
                    names=names,
                    is_relative=is_relative,
                    level=node.level,
                    lineno=node.lineno,
                ))
        
        return imports
    
    def _extract_exports(self, tree: ast.AST) -> List[str]:
        """提取导出符号（顶层定义）"""
        exports = []
        
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                exports.append(node.name)
            elif isinstance(node, ast.ClassDef):
                exports.append(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        exports.append(target.id)
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name):
                    exports.append(node.target.id)
        
        return exports
    
    def _build_dependency_graph(self) -> None:
        """构建依赖图"""
        for module_name, module_info in self.modules.items():
            for imp in module_info.imports:
                target_module = self._resolve_import(module_name, imp)
                
                if target_module and target_module in self.module_paths:
                    # 只记录项目内部的依赖
                    self.dependency_graph[module_name].add(target_module)
    
    def _resolve_import(self, source_module: str, imp: ImportInfo) -> Optional[str]:
        """
        解析导入，返回目标模块名
        
        Args:
            source_module: 源模块名
            imp: 导入信息
        
        Returns:
            目标模块名，如果无法解析则返回 None
        """
        if imp.is_relative:
            # 相对导入
            parts = source_module.split('.')
            
            # 根据 level 向上跳
            if imp.level > len(parts):
                return None
            
            base_parts = parts[:-imp.level] if imp.level <= len(parts) else []
            
            if imp.module:
                target = '.'.join(base_parts + [imp.module])
            else:
                target = '.'.join(base_parts)
            
            # 检查是否存在
            if target in self.module_paths:
                return target
            
            # 可能是包内的模块
            for name in imp.names:
                potential = f"{target}.{name}" if target else name
                if potential in self.module_paths:
                    return potential
            
            return target if target else None
        
        else:
            # 绝对导入
            module = imp.module or imp.names[0] if imp.names else ''
            
            # 检查是否是标准库或第三方库
            top_level = module.split('.')[0] if module else ''
            if top_level in self.STDLIB_MODULES or top_level in self.THIRD_PARTY_MODULES:
                return None
            
            # 检查是否是项目内部模块
            if module in self.module_paths:
                return module
            
            # 检查部分匹配
            for known_module in self.module_paths:
                if known_module.startswith(module + '.') or known_module == module:
                    return module
            
            return None
    
    def get_module_imports(self, module_name: str) -> List[ImportInfo]:
        """获取模块的所有导入"""
        return self.modules.get(module_name, ModuleInfo(path='')).imports
    
    def get_module_exports(self, module_name: str) -> List[str]:
        """获取模块的所有导出"""
        return self.modules.get(module_name, ModuleInfo(path='')).exports
    
    def get_dependents(self, module_name: str) -> List[str]:
        """获取依赖某个模块的所有模块"""
        dependents = []
        for source, targets in self.dependency_graph.items():
            if module_name in targets:
                dependents.append(source)
        return dependents
    
    def get_dependencies(self, module_name: str) -> List[str]:
        """获取模块的所有依赖"""
        return list(self.dependency_graph.get(module_name, set()))
