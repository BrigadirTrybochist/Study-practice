@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

if exist "%~dp0.venv\Scripts\pythonw.exe" (
    start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0SimulatorBankaGUI.pyw"
) else (
    where py >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        start "" py -3w "%~dp0SimulatorBankaGUI.pyw"
    ) else (
        where pythonw >nul 2>nul
        if %ERRORLEVEL% EQU 0 (
            start "" pythonw "%~dp0SimulatorBankaGUI.pyw"
        ) else (
            echo Python не знайдено. Встановіть Python 3.8+ і переконайтеся, що доступні команди py або pythonw.
            pause
            exit /b 1
        )
    )
)
