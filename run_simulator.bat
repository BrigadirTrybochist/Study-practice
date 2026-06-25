@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title Симулятор Банківського Рахунку

if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0SimulatorBanka.py"
) else (
    where py >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        py -3 "%~dp0SimulatorBanka.py"
    ) else (
        where python >nul 2>nul
        if %ERRORLEVEL% EQU 0 (
            python "%~dp0SimulatorBanka.py"
        ) else (
            echo Python не знайдено. Встановіть Python 3.8+ і переконайтеся, що доступні команди py або python.
            pause
            exit /b 1
        )
    )
)
pause
