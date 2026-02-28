@echo off
chcp 65001 >nul
echo ========================================
echo   PyVizAST - Python AST可视化分析器
echo ========================================
echo.

:: 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

:: 运行安装和启动
python run.py all
pause
