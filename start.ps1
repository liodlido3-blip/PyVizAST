# PyVizAST - Python AST可视化分析器启动脚本
# PowerShell 版本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PyVizAST - Python AST可视化分析器" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[错误] 未找到Python，请先安装Python 3.8+" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

# 检查pip
try {
    pip --version | Out-Null
    Write-Host "[OK] pip已安装" -ForegroundColor Green
} catch {
    Write-Host "[错误] 未找到pip" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

# 安装后端依赖
Write-Host ""
Write-Host "正在安装后端依赖..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] 后端依赖安装完成" -ForegroundColor Green
} else {
    Write-Host "[错误] 后端依赖安装失败" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

# 检查npm
$npmExists = Get-Command npm -ErrorAction SilentlyContinue
if ($npmExists) {
    Write-Host "[OK] npm已安装" -ForegroundColor Green
    
    # 安装前端依赖
    Write-Host ""
    Write-Host "正在安装前端依赖..." -ForegroundColor Yellow
    Push-Location frontend
    npm install
    Pop-Location
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] 前端依赖安装完成" -ForegroundColor Green
    } else {
        Write-Host "[警告] 前端依赖安装失败，将只启动后端" -ForegroundColor Yellow
    }
} else {
    Write-Host "[警告] 未找到npm，跳过前端安装" -ForegroundColor Yellow
    Write-Host "        如需前端功能，请安装Node.js" -ForegroundColor Yellow
}

# 启动服务
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  启动服务" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 启动后端
Write-Host ""
Write-Host "正在启动后端服务 (http://localhost:8000)..." -ForegroundColor Yellow

$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PSScriptRoot
    python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
}

# 等待后端启动
Start-Sleep -Seconds 3

# 检查后端是否启动成功
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "[OK] 后端服务启动成功" -ForegroundColor Green
    Write-Host "      API文档: http://localhost:8000/docs" -ForegroundColor Cyan
} catch {
    Write-Host "[警告] 后端服务可能正在启动中..." -ForegroundColor Yellow
}

# 启动前端
if ($npmExists) {
    Write-Host ""
    Write-Host "正在启动前端服务 (http://localhost:3000)..." -ForegroundColor Yellow
    
    $frontendJob = Start-Job -ScriptBlock {
        Set-Location "$using:PSScriptRoot\frontend"
        npm start
    }
    
    Write-Host "[OK] 前端服务启动中..." -ForegroundColor Green
    Write-Host "      访问地址: http://localhost:3000" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  服务已启动，按Ctrl+C停止所有服务" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 等待用户中断
try {
    while ($true) {
        # 检查后端日志
        $backendOutput = Receive-Job -Job $backendJob -ErrorAction SilentlyContinue
        if ($backendOutput) {
            Write-Host $backendOutput -ForegroundColor Gray
        }
        
        if ($npmExists -and $frontendJob) {
            $frontendOutput = Receive-Job -Job $frontendJob -ErrorAction SilentlyContinue
            if ($frontendOutput) {
                Write-Host $frontendOutput -ForegroundColor Gray
            }
        }
        
        Start-Sleep -Milliseconds 100
    }
} finally {
    Write-Host ""
    Write-Host "正在停止服务..." -ForegroundColor Yellow
    
    Stop-Job -Job $backendJob -ErrorAction SilentlyContinue
    Remove-Job -Job $backendJob -ErrorAction SilentlyContinue
    
    if ($npmExists -and $frontendJob) {
        Stop-Job -Job $frontendJob -ErrorAction SilentlyContinue
        Remove-Job -Job $frontendJob -ErrorAction SilentlyContinue
    }
    
    Write-Host "[OK] 服务已停止" -ForegroundColor Green
}
