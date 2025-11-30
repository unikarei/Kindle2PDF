@echo off
setlocal enableextensions enabledelayedexpansion
rem ========================================================================
rem Git Remote Setup Script (git_setup_remote.bat)
rem - Add remote origin interactively
rem - Set default branch and push
rem ========================================================================

rem Move to script directory (project root)
cd /d %~dp0

rem Check Git availability
where git >nul 2>nul
if errorlevel 1 (
    echo [Error] Git is not installed or not in PATH.
    pause
    exit /b 1
)

rem Check inside a Git repository
git rev-parse --is-inside-work-tree >nul 2>nul
if errorlevel 1 (
    echo [Error] This directory is not a Git repository.
    echo [Info] Run 'git init' first.
    pause
    exit /b 1
)

echo ========================================
echo       Git Remote Setup Script
echo ========================================
echo.

rem Check if remote 'origin' already exists
git remote get-url origin >nul 2>nul
if not errorlevel 1 (
    for /f "delims=" %%u in ('git remote get-url origin 2^>nul') do set EXISTING_URL=%%u
    echo [Info] Remote 'origin' already exists:
    echo        !EXISTING_URL!
    echo.
    set /p OVERWRITE="Overwrite with new URL? [y/N]: "
    if /I not "!OVERWRITE!"=="Y" (
        echo [Info] Cancelled.
        pause
        exit /b 0
    )
    git remote remove origin
    echo [Info] Removed existing remote 'origin'.
    echo.
)

rem Ask for repository URL
echo Enter your GitHub repository URL.
echo Example: https://github.com/USERNAME/REPO.git
echo      or: git@github.com:USERNAME/REPO.git
echo.
set /p REPO_URL="Repository URL: "
if "%REPO_URL%"=="" (
    echo [Error] Repository URL cannot be empty.
    pause
    exit /b 1
)

rem Add remote origin
echo.
echo Adding remote 'origin'...
git remote add origin "%REPO_URL%"
if errorlevel 1 (
    echo [Error] Failed to add remote.
    pause
    exit /b 1
)
echo [Success] Remote 'origin' added: %REPO_URL%

rem Ask for branch name
echo.
set /p BRANCH_NAME="Branch name [main]: "
if "%BRANCH_NAME%"=="" set BRANCH_NAME=main

rem Rename current branch to specified name
echo.
echo Setting branch to '%BRANCH_NAME%'...
git branch -M %BRANCH_NAME%
if errorlevel 1 (
    echo [Warning] Could not rename branch. Continuing...
)

rem Push to remote
echo.
set /p DO_PUSH="Push to remote now? [Y/n]: "
if /I "%DO_PUSH%"=="N" (
    echo.
    echo [Info] Setup complete. Run the following to push later:
    echo        git push -u origin %BRANCH_NAME%
    pause
    exit /b 0
)

echo.
echo Pushing to origin/%BRANCH_NAME% ...
git push -u origin %BRANCH_NAME%
if errorlevel 1 (
    echo.
    echo [Error] Push failed.
    echo [Info] If the remote has existing content, try:
    echo        git pull --rebase origin %BRANCH_NAME%
    echo        git push -u origin %BRANCH_NAME%
    pause
    exit /b 1
)

echo.
echo ========================================
echo [Success] Remote setup complete!
echo ========================================
echo Remote : %REPO_URL%
echo Branch : %BRANCH_NAME%
echo.
echo You can now use git_commit.bat for future commits.
echo.
pause
exit /b 0
