@echo off
setlocal
echo ========================================================
echo   RetailIQ - One-Click Push to GitHub
echo ========================================================
echo.

cd /d "%~dp0"

set DEFAULT_URL=https://github.com/Sai-Babud4/Store-IQ.git
set /p REPO_URL="Press Enter to use [%DEFAULT_URL%] or paste custom URL: "
if "%REPO_URL%"=="" set REPO_URL=%DEFAULT_URL%

echo.
echo Using repository: %REPO_URL%
echo.

echo [1/3] Configuring remote origin...
git remote remove origin 2>nul
git remote add origin %REPO_URL%

echo [2/3] Staging all files (src/, api/, data/)...
git add .
git commit -m "RetailIQ: Fullstack production deployment with resilient backend and database"

echo [3/3] Pushing to GitHub main branch...
git branch -M main
git push -u -f origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo   SUCCESS! All files and datasets pushed to GitHub!
    echo   Vercel will now automatically trigger a new deployment.
    echo ========================================================
) else (
    echo.
    echo ========================================================
    echo   [NOTE] If git requested authentication, please sign in.
    echo ========================================================
)
pause
