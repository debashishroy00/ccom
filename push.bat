@echo off
setlocal enableextensions

REM ---- Repo sanity ----
git rev-parse --is-inside-work-tree >NUL 2>&1
if errorlevel 1 (
  echo Initializing git repo...
  git init
)

REM ---- Ensure branch is main ----
for /f "tokens=*" %%b in ('git rev-parse --abbrev-ref HEAD 2^>NUL') do set CURBR=%%b
if not "%CURBR%"=="main" (
  git branch -M main
)

REM ---- Ensure correct remote ----
for /f "tokens=*" %%u in ('git remote get-url origin 2^>NUL') do set ORIGIN=%%u
if "%ORIGIN%"=="" (
  git remote add origin https://github.com/debashishroy00/ccom.git
) else (
  REM Fix wrong repo name (cco -> ccom)
  echo %ORIGIN% | findstr /I /C:"/cco.git" >NUL
  if not errorlevel 1 (
    git remote set-url origin https://github.com/debashishroy00/ccom.git
  )
)

REM ---- Stage & commit ----
git add -A

set MSG=%*
if "%MSG%"=="" set MSG=chore: update

git diff --cached --quiet
if errorlevel 1 (
  git commit -m "%MSG%"
) else (
  echo (no staged changes to commit)
)

REM ---- Sync with remote (handles existing history) ----
git fetch origin main >NUL 2>&1
git pull --rebase origin main >NUL 2>&1

REM ---- Push ----
echo Pushing to GitHub (main)...
git push -u origin main
if errorlevel 1 (
  echo.
  echo ❌ Push failed. Common fixes:
  echo   - Check credentials: gh auth login  ^(or set a PAT in credential manager^)
  echo   - Verify remote: git remote -v
  echo   - Last resort: git push --force-with-lease origin main
  exit /b 1
) else (
  echo ✅ Pushed successfully.
)

endlocal
