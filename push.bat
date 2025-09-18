@echo off
REM CCOM v0.1 - Quick commit and push to GitHub

echo Committing CCOM v0.1 to GitHub...
echo.

REM Check if git repo exists
if not exist .git (
    echo Initializing git repository...
    git init
    git remote add origin https://github.com/debashishroy00/ccom.git
)

REM Add all files
echo Adding files...
git add .

REM Check if there are changes to commit
git diff --staged --quiet
if %errorlevel% equ 0 (
    echo No changes to commit.
    pause
    exit /b 0
)

REM Commit with timestamp
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "MIN=%dt:~10,2%" & set "SS=%dt:~12,2%"
set "timestamp=%YYYY%-%MM%-%DD% %HH%:%MIN%"

git commit -m "CCOM v0.1 - Claude Code Orchestrator and Memory (%timestamp%)"

REM Push to GitHub
echo Pushing to GitHub...
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ✅ Successfully pushed to GitHub!
    echo.
    echo Ready for PyPI:
    echo   pip install build twine
    echo   python -m build
    echo   python -m twine upload dist/*
    echo.
    echo Test install:
    echo   pip install ccom
    echo   ccom init
) else (
    echo.
    echo ❌ Push failed. Check your GitHub credentials.
)

echo.
pause