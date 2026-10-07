@echo off
rem Belge Tabanli Soru Asistani - otomatik testleri calistirir (Windows). Cift tikla.
chcp 65001 >nul
cd /d "%~dp0"

set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY ( where python >nul 2>nul && set "PY=python" )
if not defined PY (
    echo Python bulunamadi. Python 3.10 veya ustunu kurun: https://www.python.org/downloads/
    pause
    exit /b 1
)

if not exist "venv\Scripts\python.exe" (
    echo Sanal ortam olusturuluyor...
    %PY% -m venv venv || goto :hata
)
echo Test paketleri kontrol ediliyor...
"venv\Scripts\python.exe" -m pip install -q --disable-pip-version-check -r requirements-dev.txt || goto :hata
echo.
"venv\Scripts\python.exe" -m pytest
echo.
pause
exit /b 0

:hata
echo HATA olustu. Yukaridaki mesaji okuyun.
pause
exit /b 1
