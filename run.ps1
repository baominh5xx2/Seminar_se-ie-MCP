# ============================================================================
# AI Assistant MCP Server - Run Script (PowerShell)
# Chạy MCP server với UV package manager
# ============================================================================

Write-Host "🚀 Starting AI Assistant MCP Server with UV..." -ForegroundColor Cyan
Write-Host ""

# Kiểm tra UV đã cài đặt chưa
try {
    $uvVersion = uv --version 2>&1
    Write-Host "✅ UV version: $uvVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ UV chưa được cài đặt!" -ForegroundColor Red
    Write-Host "   Cài đặt UV: irm https://astral.sh/uv/install.ps1 | iex" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Kiểm tra file .env
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  File .env không tồn tại. Tạo từ .env.example..." -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "✅ Đã tạo file .env" -ForegroundColor Green
        Write-Host "   Vui lòng cập nhật BACKEND_API_URL và các config khác!" -ForegroundColor Yellow
    } else {
        Write-Host "❌ File .env.example không tồn tại!" -ForegroundColor Red
        exit 1
    }
    Write-Host ""
}

# Kiểm tra Backend API
Write-Host "🔍 Kiểm tra Backend API..." -ForegroundColor Cyan
try {
    $backendUrl = if ($env:BACKEND_API_URL) { $env:BACKEND_API_URL } else { "http://localhost:8000" }
    $response = Invoke-WebRequest -Uri "$backendUrl/health" -UseBasicParsing -TimeoutSec 5 2>&1
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Backend API đang chạy tại $backendUrl" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Backend API không phản hồi tại $backendUrl" -ForegroundColor Yellow
    Write-Host "   Đảm bảo Backend đang chạy trước khi sử dụng MCP server!" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Gray

# Tạo venv nếu chưa có
if (-not (Test-Path ".venv")) {
    Write-Host "📦 Tạo virtual environment..." -ForegroundColor Cyan
    uv venv
    Write-Host "✅ Đã tạo .venv" -ForegroundColor Green
    Write-Host ""
}

# Cài đặt dependencies
Write-Host "📦 Cài đặt dependencies với UV..." -ForegroundColor Cyan
uv pip install fastmcp python-dotenv pydantic httpx aiofiles

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Gray
Write-Host ""

# Chạy server
Write-Host "🎯 Starting MCP Server..." -ForegroundColor Green
Write-Host "   Server: AI Assistant MCP" -ForegroundColor White
Write-Host "   File: server.py" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""
Write-Host "=" * 70 -ForegroundColor Gray
Write-Host ""

# Run với UV
uv run server.py
