@echo off
title Discord AI Bot - Auto-Install and Run Script
color 0B

echo =============================================
echo [BOT] Discord AI Bot - Auto-Install and Run Script
echo =============================================
echo.

REM Check if Python is installed
echo [CHECK] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check 'Add Python to PATH' during installation.
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('python --version') do set python_version=%%i
    echo [SUCCESS] Python is installed: %python_version%
)

REM Check if pip is installed
echo.
echo [CHECK] Checking pip installation...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pip is not installed or not in PATH!
    echo Please install pip or reinstall Python.
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('pip --version') do set pip_version=%%i
    echo [SUCCESS] pip is installed: %pip_version%
)

REM Install required packages
echo.
echo [INSTALL] Installing required packages...
pip install -r requirements.txt >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install packages!
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
) else (
    echo [SUCCESS] Packages installed successfully!
)

REM Check if .env file exists
echo.
echo [CHECK] Checking .env file...
if not exist .env (
    echo [WARNING] .env file not found!
    echo Creating a new .env file...
    
    REM Create .env file
    echo. > .env
    
    REM Ask for Discord token
    echo Please enter your Discord bot token:
    set /p discord_token=
    
    REM Ask for Google API key
    echo Please enter your Google API key:
    set /p google_api_key=
    
    REM Write to .env file
    echo DISCORD_TOKENS=%discord_token% > .env
    echo GOOGLE_API_KEYS=%google_api_key% >> .env
    
    echo [SUCCESS] .env file created successfully!
) else (
    echo [SUCCESS] .env file found!
    
    REM Check if .env file has required variables
    findstr /C:"DISCORD_TOKENS=" .env >nul
    if %errorlevel% neq 0 (
        echo [WARNING] DISCORD_TOKENS not found in .env file!
        echo Please enter your Discord bot token:
        set /p discord_token=
        echo DISCORD_TOKENS=%discord_token% >> .env
    )
    
    findstr /C:"GOOGLE_API_KEYS=" .env >nul
    if %errorlevel% neq 0 (
        echo [WARNING] GOOGLE_API_KEYS not found in .env file!
        echo Please enter your Google API key:
        set /p google_api_key=
        echo GOOGLE_API_KEYS=%google_api_key% >> .env
    )
)

REM Check if logs directory exists
echo.
echo [CHECK] Checking logs directory...
if not exist logs (
    echo Creating logs directory...
    mkdir logs
    echo [SUCCESS] Logs directory created successfully!
) else (
    echo [SUCCESS] Logs directory found!
)

REM Start the bot
echo.
echo =============================================
echo [START] Starting Discord AI Bot...
echo =============================================
echo The bot will now start. Follow the on-screen instructions to configure it.
echo Press Ctrl+C to stop the bot when you're done.
echo =============================================
echo.

REM Run the bot
python bot.py

REM Wait for user to press a key before exiting
echo.
echo Press any key to exit...
pause >nul 