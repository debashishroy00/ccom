@echo off
echo CCOM v0.3 - Pushing changes to GitHub...
echo.

REM Show what we have
echo Current status:
git status
echo.

REM Add all changes
echo Adding all changes...
git add .
echo.

REM Show what will be committed
echo Changes to commit:
git status --short
echo.

REM Commit with v0.3 message
echo Committing...
git commit -m "CCOM v0.3 - Claude Code Integration with prefix-based activation"

REM Push to GitHub
echo Pushing to GitHub...
git push origin main

echo.
echo Done! Check GitHub to verify the changes were pushed.
pause