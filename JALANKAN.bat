@echo off
setlocal
title Sahamian
cd /d "%~dp0"

echo.
echo  ============================================
echo   SAHAMIAN  -  Analisis Saham IDX
echo  ============================================
echo.

REM ---------- cek Python ^& Node ----------
where python >nul 2>nul
if errorlevel 1 (
    echo  [X] Python tidak ditemukan.
    echo.
    echo      Pasang Python 3.11 atau lebih baru dari:
    echo      https://www.python.org/downloads/
    echo.
    echo      PENTING: saat memasang, centang "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
    echo  [X] Node.js tidak ditemukan.
    echo.
    echo      Pasang Node.js dari: https://nodejs.org/
    echo.
    pause
    exit /b 1
)

REM ---------- setup otomatis kalau belum ada ----------
if not exist "idx\.venv\Scripts\python.exe" (
    echo  [1/3] Menyiapkan Python environment ^(sekali saja, ~2 menit^)...
    python -m venv idx\.venv
    if errorlevel 1 ( echo  [X] Gagal membuat venv. & pause & exit /b 1 )
    idx\.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
    idx\.venv\Scripts\pip.exe install -r idx\requirements.txt --quiet
    if errorlevel 1 ( echo  [X] Gagal memasang paket Python. & pause & exit /b 1 )
    echo        selesai.
) else (
    echo  [1/3] Python environment sudah siap.
)

if not exist "idx\dashboard\node_modules" (
    echo  [2/3] Memasang dependensi tampilan ^(sekali saja, ~2 menit^)...
    pushd idx\dashboard
    call npm install --silent
    if errorlevel 1 ( echo  [X] Gagal npm install. & popd & pause & exit /b 1 )
    popd
    echo        selesai.
) else (
    echo  [2/3] Dependensi tampilan sudah siap.
)

if not exist "idx\data\BBCA.csv" (
    echo  [3/3] Menarik data harga saham pertama kali ^(~3 menit^)...
    pushd idx
    .venv\Scripts\python.exe download_data.py
    .venv\Scripts\python.exe download_extra.py
    .venv\Scripts\python.exe build_ticker_names.py
    popd
    echo        selesai.
) else (
    echo  [3/3] Data harga sudah ada.
)

REM ---------- bebaskan port yang masih nyangkut ----------
echo.
echo  Membersihkan sisa server lama...
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:"TCP.*:8000 .*LISTENING"') do taskkill /F /PID %%P >nul 2>nul
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:"TCP.*:5173 .*LISTENING"') do taskkill /F /PID %%P >nul 2>nul

REM ---------- jalankan kedua server ----------
REM start /d menetapkan folder kerja, jadi tidak perlu "cd" bertanda kutip di dalam
REM perintah - itu yang bikin kutip bersarang dan rapuh kalau path mengandung spasi.
echo  Menjalankan server...
start "IDX - Server Data (jangan ditutup)" /min /d "%~dp0idx" cmd /k .venv\Scripts\python.exe -m uvicorn app.server:api --port 8000 --reload --reload-dir . --app-dir .
start "IDX - Server Tampilan (jangan ditutup)" /min /d "%~dp0idx\dashboard" cmd /k npm run dev

REM ---------- tunggu sampai siap ----------
REM Pakai ping sebagai jeda, bukan "timeout": timeout gagal ("Input redirection is not
REM supported") kalau skrip dijalankan dari proses lain yang mengalihkan stdin.
echo  Menunggu server siap...
set /a tries=0
:tunggu
ping -n 3 127.0.0.1 >nul 2>nul
set /a tries+=1
curl -s -o nul http://localhost:5173 >nul 2>nul
if not errorlevel 1 goto siap
if %tries% lss 25 goto tunggu
echo  [!] Server lebih lama dari biasanya. Coba buka manual: http://localhost:5173

:siap
start "" http://localhost:5173

echo.
echo  ============================================
echo   APLIKASI BERJALAN
echo.
echo   Buka di browser: http://localhost:5173
echo.
echo   Dua jendela kecil terbuka di taskbar
echo   ^(Server Data ^& Server Tampilan^).
echo   JANGAN ditutup selama memakai aplikasi.
echo.
echo   Untuk berhenti: jalankan HENTIKAN.bat
echo  ============================================
echo.
echo  Jendela ini akan tertutup sendiri.
ping -n 10 127.0.0.1 >nul 2>nul
