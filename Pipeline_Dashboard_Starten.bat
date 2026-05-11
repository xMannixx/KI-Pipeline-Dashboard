@echo off
title Aethos Pipeline Dashboard
chcp 65001 >nul

:: ─── Projektpfad ────────────────────────────────────────────────────────────
set PROJECT_DIR=%~dp0
:: ────────────────────────────────────────────────────────────────────────────

:: API Keys optional hier eintragen (oder als .env Datei im Projektordner)
:: set GOOGLE_API_KEY=AIza...
:: set ANTHROPIC_API_KEY=sk-ant-...
:: set OPENAI_API_KEY=sk-...
:: set DEEPSEEK_API_KEY=sk-...

cd /d "%PROJECT_DIR%"

if not exist "app.py" (
    echo.
    echo   FEHLER: app.py nicht gefunden in:
    echo   %PROJECT_DIR%
    pause
    exit /b 1
)

echo.
echo   *** Aethos Pipeline Dashboard ***
echo.
echo   Browser oeffnet automatisch auf http://localhost:5000
echo   Stoppen: Fenster schliessen oder Ctrl+C
echo.

python app.py

pause
