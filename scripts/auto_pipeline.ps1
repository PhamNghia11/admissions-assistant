<#
.SYNOPSIS
    Script tự động hóa Data Pipeline: Cập nhật dữ liệu Tuyển sinh 
    từ Internet và Nạp trực tiếp vào Não bộ AI (LanceDB).

.DESCRIPTION
    Bước 1: Chạy crawler để quét dữ liệu website các trường.
    Bước 2: Quay lại agent và chạy script Ingestion để nạp JSON & Metadata.
#>

$ErrorActionPreference = "Stop"

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "🚀 KHỞI ĐỘNG CRAWLER TUYỂN SINH (AUTO-MODE)" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# 1. Chuyển hướng sang thư mục Crawler
Set-Location -Path "d:\tuyen_sinh_project"
Write-Host "[1/2] Đang kích hoạt Crawl Data thời gian thực..." -ForegroundColor Yellow

# Tắt warning và chạy python crawler
$env:PYTHONIOENCODING="utf-8"
python crawl.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Lỗi khi chạy Crawler! Dừng quy trình." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "✅ Crawler hoàn tất xuất sắc." -ForegroundColor Green

# 2. Quay lại thư mục Agent
Write-Host "`n=============================================" -ForegroundColor Cyan
Write-Host "🧠 NẠP DỮ LIỆU ĐỘNG VÀO NÃO BỘ AI" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Set-Location -Path "d:\agent"

Write-Host "[2/2] Đang phân rã dữ liệu và nạp Vector Metadata..." -ForegroundColor Yellow
python scripts/ingest_admissions.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Lỗi khi nạp dữ liệu vào AI!" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "✅ QUY TRÌNH HOÀN TẤT! AI ĐÃ ĐƯỢC CẬP NHẬT THẾ GIỚI MỚI NHẤT." -ForegroundColor Green
