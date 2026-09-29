@echo off
setlocal enabledelayedexpansion
title Hentikan Analisis Saham IDX
echo.
echo  Menghentikan server Analisis Saham IDX...
echo.

set found=0

REM 1) Tutup jendela server berdasarkan judulnya. Ini yang utama: jendela dibuka dengan
REM    "cmd /k" sehingga tetap terbuka walau proses anaknya sudah mati.
for %%T in ("IDX - Server Data*" "IDX - Server Tampilan*") do (
    taskkill /F /FI "WINDOWTITLE eq %%~T" /T >nul 2>nul
    if not errorlevel 1 set found=1
)

REM 2) Cadangan: kalau masih ada yang memegang port, hentikan juga.
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:"TCP.*:8000 .*LISTENING"') do (
    taskkill /F /PID %%P /T >nul 2>nul
    if not errorlevel 1 set found=1
)
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:"TCP.*:5173 .*LISTENING"') do (
    taskkill /F /PID %%P /T >nul 2>nul
    if not errorlevel 1 set found=1
)

if "!found!"=="1" (
    echo    Server dihentikan.
) else (
    echo    Tidak ada server yang sedang berjalan.
)

echo.
echo  Catatan: kalau "netstat" masih menampilkan port 8000 sebagai TIME_WAIT,
echo  itu normal dan hilang sendiri dalam beberapa menit. Tidak menghalangi
echo  JALANKAN.bat dipakai lagi.
echo.
ping -n 5 127.0.0.1 >nul 2>nul
