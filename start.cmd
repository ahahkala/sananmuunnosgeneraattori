@echo off
REM Kaynnistaa sananmuunnosgeneraattorin paikalliseen selaimeen.
cd /d "%~dp0web"
start "" http://localhost:8000/
python -m http.server 8000
