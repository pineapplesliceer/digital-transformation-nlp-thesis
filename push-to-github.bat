@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ============================================================
echo   Push this thesis repo to GitHub
echo ============================================================
echo.
echo   IMPORTANT: create an EMPTY repo on GitHub first:
echo     https://github.com/new
echo     Repository name : digital-transformation-nlp-thesis
echo     Initialize with README / .gitignore / license : DO NOT check any
echo.
echo   Then come back here and press a key.
echo.
pause >nul

set REPO=digital-transformation-nlp-thesis
set /p GHUSER=Your GitHub username: 

if "%GHUSER%"=="" (
  echo [ERROR] Username cannot be empty.
  pause
  exit /b 1
)

echo.
echo [1/4] Configuring remote origin ...
git remote remove origin >nul 2>&1
git remote add origin https://github.com/%GHUSER%/%REPO%.git
if errorlevel 1 goto :fail

echo [2/4] Renaming branch to main ...
git branch -M main
if errorlevel 1 goto :fail

echo [3/4] Pushing (a browser window may pop up for GitHub login) ...
git push -u origin main
if errorlevel 1 goto :fail

echo [4/4] Done.
echo.
echo ============================================================
echo   Repository : https://github.com/%GHUSER%/%REPO%
echo   Web paper  : https://%GHUSER%.github.io/%REPO%/   (enable Pages: Settings - Pages - main /docs)
echo   Word file  : https://github.com/%GHUSER%/%REPO%/blob/main/paper/
echo ============================================================
echo.
pause
exit /b 0

:fail
echo.
echo [FAILED] Check the message above.
echo   - If it says "repository not found", the repo was not created yet,
echo     or the username is wrong.
echo   - If login fails, retry and complete the browser authorization.
echo.
pause
exit /b 1
