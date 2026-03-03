"""
Project Scanner - 扫描项目目录，发现 Python 文件
"""
import os
import zipfile
import tempfile
import shutil
import time
import ast
from pathlib import Path
from typing import List, Optional, Set, Tuple
from dataclasses import dataclass

from .models import FileInfo, ProjectScanResult
from ..utils.logger import get_logger

logger = get_logger(__name__)


# 默认忽略的目录
DEFAULT_IGNORE_DIRS = {
    '__pycache__',
    '.git',
    '.svn',
    '.hg',
    'node_modules',
    'venv',
    '.venv',
    'env',
    '.env',
    'dist',
    'build',
    'egg-info',
    '.eggs',
    '.mypy_cache',
    '.pytest_cache',
    '.tox',
    'htmlcov',
    '.idea',
    '.vscode',
}

# 默认忽略的文件模式
DEFAULT_IGNORE_PATTERNS = {
    'setup.py',
    'conftest.py',
}


class ProjectScanner:
    """项目扫描器"""
    
    def __init__(self, ignore_dirs: Optional[Set[str]] = None,
                 ignore_patterns: Optional[Set[str]] = None,
                 max_file_size: int = 5 * 1024 * 1024,  # 5MB
                 max_files: int = 1000):
        """
        初始化扫描器
        
        Args:
            ignore_dirs: 忽略的目录名
            ignore_patterns: 忽略的文件模式
            max_file_size: 单文件最大大小（字节）
            max_files: 最大文件数量
        """
        self.ignore_dirs = ignore_dirs or DEFAULT_IGNORE_DIRS
        self.ignore_patterns = ignore_patterns or DEFAULT_IGNORE_PATTERNS
        self.max_file_size = max_file_size
        self.max_files = max_files
    
    def scan_zip(self, zip_path: str, project_name: Optional[str] = None) -> Tuple[ProjectScanResult, str]:
        """
        扫描 ZIP 压缩包
        
        Args:
            zip_path: ZIP 文件路径
            project_name: 项目名称（可选）
        
        Returns:
            (扫描结果, 临时目录路径)
        """
        start_time = time.time()
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix='pyvizast_')
        
        try:
            # 解压 ZIP 文件
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # 查找项目根目录
            project_root = self._find_project_root(temp_dir)
            
            if project_name is None:
                project_name = Path(zip_path).stem
            
            # 扫描目录
            result = self.scan_directory(project_root, project_name)
            result.scan_time_ms = (time.time() - start_time) * 1000
            
            return result, project_root
            
        except Exception as e:
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise RuntimeError(f"解压 ZIP 文件失败: {str(e)}")
    
    def scan_directory(self, directory: str, project_name: str) -> ProjectScanResult:
        """
        扫描目录
        
        Args:
            directory: 目录路径
            project_name: 项目名称
        
        Returns:
            扫描结果
        """
        start_time = time.time()
        
        directory = Path(directory).resolve()
        file_infos: List[FileInfo] = []
        skipped_files: List[str] = []
        
        for root, dirs, files in os.walk(directory):
            # 过滤忽略的目录
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs and not d.startswith('.')]
            
            for filename in files:
                if not filename.endswith('.py'):
                    continue
                
                file_path = Path(root) / filename
                relative_path = file_path.relative_to(directory)
                
                # 检查是否应该忽略
                if self._should_ignore_file(relative_path):
                    skipped_files.append(str(relative_path))
                    continue
                
                # 检查文件大小
                try:
                    file_size = file_path.stat().st_size
                except OSError:
                    continue
                
                if file_size > self.max_file_size:
                    skipped_files.append(str(relative_path))
                    logger.warning(f"文件过大，跳过: {relative_path} ({file_size} bytes)")
                    continue
                
                # 检查文件数量限制
                if len(file_infos) >= self.max_files:
                    logger.warning(f"达到最大文件数量限制 ({self.max_files})")
                    break
                
                # 获取文件信息
                file_info = self._get_file_info(file_path, relative_path)
                file_infos.append(file_info)
        
        # 构建结果
        result = ProjectScanResult(
            project_name=project_name,
            total_files=len(file_infos),
            total_size=sum(f.size for f in file_infos),
            file_paths=[f.relative_path for f in file_infos],
            file_infos=file_infos,
            skipped_count=len(skipped_files),
            skipped_files=skipped_files,
            scan_time_ms=(time.time() - start_time) * 1000,
        )
        
        logger.info(f"扫描完成: {result.total_files} 个 Python 文件, "
                   f"{result.skipped_count} 个已跳过")
        
        return result
    
    def _find_project_root(self, directory: str) -> str:
        """
        查找项目根目录（包含 pyproject.toml, setup.py, requirements.txt 等）
        """
        directory = Path(directory)
        
        # 项目根目录标志文件
        root_markers = {
            'pyproject.toml',
            'setup.py',
            'setup.cfg',
            'requirements.txt',
            'Pipfile',
            'poetry.lock',
        }
        
        # 首先检查根目录是否包含这些标志
        for marker in root_markers:
            if (directory / marker).exists():
                return str(directory)
        
        # 检查子目录
        for item in directory.iterdir():
            if item.is_dir():
                for marker in root_markers:
                    if (item / marker).exists():
                        return str(item)
        
        # 如果没有找到，检查是否有 src 目录
        src_dir = directory / 'src'
        if src_dir.exists() and src_dir.is_dir():
            return str(src_dir)
        
        # 返回原始目录
        return str(directory)
    
    def _should_ignore_file(self, relative_path: Path) -> bool:
        """检查是否应该忽略文件"""
        # 检查文件名模式
        if relative_path.name in self.ignore_patterns:
            return True
        
        # 检查路径中是否包含忽略的目录
        for part in relative_path.parts[:-1]:
            if part in self.ignore_dirs:
                return True
        
        return False
    
    def _get_file_info(self, file_path: Path, relative_path: Path) -> FileInfo:
        """获取文件信息"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            line_count = content.count('\n') + 1
        except Exception:
            line_count = 0
        
        # 检查是否是特殊文件
        name = file_path.name
        is_test = name.startswith('test_') or name.endswith('_test.py')
        is_init = name == '__init__.py'
        is_main = name == '__main__.py'
        
        return FileInfo(
            path=str(file_path),
            relative_path=str(relative_path).replace('\\', '/'),
            size=file_path.stat().st_size,
            line_count=line_count,
            is_test=is_test,
            is_init=is_init,
            is_main=is_main,
        )
    
    @staticmethod
    def count_lines(content: str) -> int:
        """统计代码行数（排除空行和注释）"""
        try:
            tree = ast.parse(content)
            # 简单统计：总行数 - 空行 - 纯注释行
            lines = content.split('\n')
            code_lines = 0
            in_multiline_string = False
            
            for line in lines:
                stripped = line.strip()
                
                # 跳过空行
                if not stripped:
                    continue
                
                # 跳过单行注释
                if stripped.startswith('#'):
                    continue
                
                code_lines += 1
            
            return code_lines
        except SyntaxError:
            # 如果解析失败，返回简单的行数统计
            return len([l for l in content.split('\n') if l.strip() and not l.strip().startswith('#')])
