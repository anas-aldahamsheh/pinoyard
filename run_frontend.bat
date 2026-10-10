@echo off
title Pino Yard Frontend (Next.js)
cd /d "%~dp0"
echo ==============================================
echo   Starting Pino Yard Frontend on :3000 ...
echo ==============================================
npm --prefix apps/web run dev
pause
