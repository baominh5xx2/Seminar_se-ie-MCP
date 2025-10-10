# ============================================================================
# Setup Script - Cài đặt môi trường cho MCP Server
# ============================================================================

Write-Host "🔧 Setting up MCP Server Environment..." -ForegroundColor Cyan
Write-Host ""

# 1. Kiểm tra UV
Write-Host "Step 1: Kiểm tra UV..." -ForegroundColor Yellow
try {
    $uvVersion = uv --version 2>&1
    Write-Host "✅ UV đã cài đặt: $uvVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ UV chưa được cài đặt!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Cài đặt UV ngay bây giờ? (Y/N): " -NoNewline -ForegroundColor Yellow
    $response = Read-Host
    
    if ($response -eq "Y" -or $response -eq "y") {
        Write-Host "📥 Đang cài đặt UV..." -ForegroundColor Cyan
        irm https://astral.sh/uv/install.ps1 | iex
        Write-Host "✅ Đã cài đặt UV" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Bạn cần cài UV để tiếp tục!" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""

# 2. Tạo virtual environment
Write-Host "Step 2: Tạo virtual environment..." -ForegroundColor Yellow
if (Test-Path ".venv") {
    Write-Host "✅ Virtual environment đã tồn tại" -ForegroundColor Green
} else {
    uv venv
    Write-Host "✅ Đã tạo virtual environment" -ForegroundColor Green
}

Write-Host ""

# 3. Cài đặt dependencies
Write-Host "Step 3: Cài đặt dependencies..." -ForegroundColor Yellow
uv pip install fastmcp python-dotenv pydantic httpx aiofiles
Write-Host "✅ Đã cài đặt tất cả dependencies" -ForegroundColor Green

Write-Host ""

# 4. Tạo file .env
Write-Host "Step 4: Cấu hình environment..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✅ File .env đã tồn tại" -ForegroundColor Green
} else {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "✅ Đã tạo file .env từ .env.example" -ForegroundColor Green
        Write-Host "⚠️  Nhớ cập nhật các giá trị trong .env!" -ForegroundColor Yellow
    } else {
        Write-Host "❌ File .env.example không tồn tại" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Gray
Write-Host "✨ Setup hoàn tất!" -ForegroundColor Green
Write-Host ""
Write-Host "Các bước tiếp theo:" -ForegroundColor Cyan
Write-Host "  1. Cập nhật file .env với BACKEND_API_URL" -ForegroundColor White
Write-Host "  2. Đảm bảo Backend API đang chạy (port 8000)" -ForegroundColor White
Write-Host "  3. Chạy server: .\run.ps1 hoặc .\start.ps1" -ForegroundColor White
Write-Host ""
Write-Host "=" * 70 -ForegroundColor Gray
