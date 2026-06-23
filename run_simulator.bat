@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Симулятор Банківського Рахунку
python "%~dp0SimulatorBanka.py"
pause
