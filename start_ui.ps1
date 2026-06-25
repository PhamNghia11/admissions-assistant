# Script khoi dong nhanh Giao dien React UI
# Yeu cau: Ban can cai dat Node.js tren may

Write-Host "Dang khoi dong Giao dien React UI..." -ForegroundColor Cyan

# Di chuyen vao thu muc UI
Set-Location -Path ".\ui-agent"

# Kiem tra xem node_modules da co chua, neu chua thi chay npm install
if (-not (Test-Path -Path "node_modules")) {
    Write-Host "Lan dau tien chay, dang cai dat thu vien (npm install)... Vui long cho." -ForegroundColor Yellow
    npm install
}

Write-Host "Dang chay Vite dev server..." -ForegroundColor Green
npm run dev
