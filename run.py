"""
PyVizAST - Python AST可视化与优化分析器
启动脚本
"""
import os
import sys
import subprocess
import argparse


def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("错误: 需要Python 3.8或更高版本")
        sys.exit(1)
    print(f"✓ Python版本: {sys.version.split()[0]}")


def install_backend_deps():
    """安装后端依赖"""
    print("\n正在安装后端依赖...")
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    
    try:
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', requirements_path],
            check=True
        )
        print("✓ 后端依赖安装完成")
    except subprocess.CalledProcessError as e:
        print(f"✗ 后端依赖安装失败: {e}")
        sys.exit(1)


def install_frontend_deps():
    """安装前端依赖"""
    print("\n正在安装前端依赖...")
    frontend_path = os.path.join(os.path.dirname(__file__), 'frontend')
    
    # 检查npm是否可用
    try:
        subprocess.run(['npm', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ 未找到npm，请先安装Node.js")
        return False
    
    try:
        subprocess.run(['npm', 'install'], cwd=frontend_path, check=True)
        print("✓ 前端依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 前端依赖安装失败: {e}")
        return False


def start_backend(host='0.0.0.0', port=8000):
    """启动后端服务"""
    print(f"\n正在启动后端服务 (http://{host}:{port})...")
    
    backend_path = os.path.dirname(__file__)
    sys.path.insert(0, backend_path)
    
    import uvicorn
    from backend.main import app
    
    uvicorn.run(app, host=host, port=port)


def start_frontend(port=3000):
    """启动前端服务"""
    print(f"\n正在启动前端服务 (http://localhost:{port})...")
    
    frontend_path = os.path.join(os.path.dirname(__file__), 'frontend')
    
    try:
        subprocess.run(['npm', 'start'], cwd=frontend_path)
    except KeyboardInterrupt:
        print("\n前端服务已停止")


def main():
    parser = argparse.ArgumentParser(
        description='PyVizAST - Python AST可视化与优化分析器'
    )
    parser.add_argument(
        'command',
        choices=['install', 'backend', 'frontend', 'start', 'all'],
        help='命令: install=安装依赖, backend=启动后端, frontend=启动前端, start=启动全部, all=安装并启动'
    )
    parser.add_argument('--host', default='0.0.0.0', help='后端服务地址')
    parser.add_argument('--port', type=int, default=8000, help='后端服务端口')
    parser.add_argument('--frontend-port', type=int, default=3000, help='前端服务端口')
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("  PyVizAST - Python AST可视化与优化分析器")
    print("=" * 50)
    
    check_python_version()
    
    if args.command == 'install':
        install_backend_deps()
        install_frontend_deps()
        
    elif args.command == 'backend':
        start_backend(args.host, args.port)
        
    elif args.command == 'frontend':
        start_frontend(args.frontend_port)
        
    elif args.command == 'start':
        # 在Windows上使用多进程启动
        import multiprocessing
        
        backend_process = multiprocessing.Process(
            target=start_backend,
            args=(args.host, args.port)
        )
        
        backend_process.start()
        
        # 等待后端启动
        import time
        time.sleep(2)
        
        try:
            start_frontend(args.frontend_port)
        except KeyboardInterrupt:
            pass
        finally:
            backend_process.terminate()
            
    elif args.command == 'all':
        install_backend_deps()
        if install_frontend_deps():
            import multiprocessing
            import time
            
            backend_process = multiprocessing.Process(
                target=start_backend,
                args=(args.host, args.port)
            )
            
            backend_process.start()
            time.sleep(2)
            
            try:
                start_frontend(args.frontend_port)
            except KeyboardInterrupt:
                pass
            finally:
                backend_process.terminate()


if __name__ == '__main__':
    main()
