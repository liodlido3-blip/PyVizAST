#!/bin/bash
echo "========================================"
echo "  PyVizAST - Python AST可视化分析器"
echo "========================================"
echo

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python，请先安装Python 3.8+"
    exit 1
fi

# 运行安装和启动
python3 run.py all
