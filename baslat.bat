@echo off
rem P55 - tek tikla kurulum ve calistirma (Windows). Cift tikla.
chcp 65001 >nul
cd /d "%~dp0"

rem 1) Python'u bul (once "py" baslaticisi, yoksa "python")
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY ( where python >nul 2>nul && set "PY=python" )
if not defined PY goto :python_yok
%PY% -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" || goto :python_eski

rem 2) Sanal ortam
if not exist "venv\Scripts\python.exe" (
    echo [1/4] Sanal ortam olusturuluyor...
    %PY% -m venv venv || goto :hata
)

rem 3) Paketler (ilk seferde birkac dakika surer; sonra hizli gecer)
echo [2/4] Paketler kontrol ediliyor...
"venv\Scripts\python.exe" -m pip install -q --disable-pip-version-check -r requirements-local.txt || goto :hata

rem 4) .env (yoksa olusturulur, varsa dokunulmaz)
echo [3/4] Ayar dosyasi (.env) kontrol ediliyor...
"venv\Scripts\python.exe" -m scripts.env_olustur || goto :hata

rem 5) Calistir ve tarayiciyi ac (port: P55_PORT ortam degiskeni, yoksa 8000)
if not defined P55_PORT set "P55_PORT=8000"
echo [4/4] Backend (API) baslatiliyor: http://127.0.0.1:%P55_PORT%/docs
echo       Arayuz icin ayrica: P55-RAG-Assistant-frontend klasorundeki baslat.bat
echo       Ilk belge yuklemesinde embedding modeli (~470 MB) bir kez indirilir.
echo       Kapatmak icin bu pencerede Ctrl+C.
start "" cmd /c "timeout /t 5 >nul & start http://127.0.0.1:%P55_PORT%/docs"
"venv\Scripts\python.exe" -m uvicorn app.main:app --port %P55_PORT%
goto :eof

:python_yok
echo Python bulunamadi. Python 3.10 veya ustunu kurun: https://www.python.org/downloads/
echo Kurulumda "Add python.exe to PATH" kutusunu isaretleyin.
pause
exit /b 1

:python_eski
echo Python surumu eski. Bu proje Python 3.10 veya ustunu ister: https://www.python.org/downloads/
pause
exit /b 1

:hata
echo.
echo HATA olustu. Yukaridaki mesaji okuyun (internet baglantisi? disk alani?).
pause
exit /b 1
