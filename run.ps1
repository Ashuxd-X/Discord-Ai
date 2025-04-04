# Discord AI Bot Auto-Install and Run Script
# This script will automatically install dependencies, set up the environment, and start the bot

# Set console colors
$host.UI.RawUI.ForegroundColor = "Cyan"
Write-Host "🤖 Discord AI Bot - Auto-Install and Run Script" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
$host.UI.RawUI.ForegroundColor = "White"

# Check if Python is installed
Write-Host "🔍 Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "✅ Python is installed: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python is not installed or not in PATH!" -ForegroundColor Red
    Write-Host "Please install Python from https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host "Make sure to check 'Add Python to PATH' during installation." -ForegroundColor Red
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit
}

# Check if pip is installed
Write-Host "🔍 Checking pip installation..." -ForegroundColor Yellow
try {
    $pipVersion = pip --version
    Write-Host "✅ pip is installed: $pipVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ pip is not installed or not in PATH!" -ForegroundColor Red
    Write-Host "Please install pip or reinstall Python." -ForegroundColor Red
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit
}

# Install required packages
Write-Host "📦 Installing required packages..." -ForegroundColor Yellow
try {
    pip install -r requirements.txt
    Write-Host "✅ Packages installed successfully!" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to install packages!" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit
}

# Check if .env file exists
Write-Host "🔍 Checking .env file..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "⚠️ .env file not found!" -ForegroundColor Yellow
    Write-Host "Creating a new .env file..." -ForegroundColor Yellow
    
    # Create .env file
    New-Item -Path ".env" -ItemType "file" -Force | Out-Null
    
    # Ask for Discord token
    Write-Host "Please enter your Discord bot token:" -ForegroundColor Cyan
    $discordToken = Read-Host
    
    # Ask for Google API key
    Write-Host "Please enter your Google API key:" -ForegroundColor Cyan
    $googleApiKey = Read-Host
    
    # Write to .env file
    "DISCORD_TOKENS=$discordToken" | Out-File -FilePath ".env" -Encoding utf8
    "GOOGLE_API_KEYS=$googleApiKey" | Out-File -FilePath ".env" -Encoding utf8 -Append
    
    Write-Host "✅ .env file created successfully!" -ForegroundColor Green
} else {
    Write-Host "✅ .env file found!" -ForegroundColor Green
    
    # Check if .env file has required variables
    $envContent = Get-Content ".env" -Raw
    if (-not ($envContent -match "DISCORD_TOKENS=")) {
        Write-Host "⚠️ DISCORD_TOKENS not found in .env file!" -ForegroundColor Yellow
        Write-Host "Please enter your Discord bot token:" -ForegroundColor Cyan
        $discordToken = Read-Host
        "DISCORD_TOKENS=$discordToken" | Out-File -FilePath ".env" -Encoding utf8 -Append
    }
    
    if (-not ($envContent -match "GOOGLE_API_KEYS=")) {
        Write-Host "⚠️ GOOGLE_API_KEYS not found in .env file!" -ForegroundColor Yellow
        Write-Host "Please enter your Google API key:" -ForegroundColor Cyan
        $googleApiKey = Read-Host
        "GOOGLE_API_KEYS=$googleApiKey" | Out-File -FilePath ".env" -Encoding utf8 -Append
    }
}

# Check if logs directory exists
Write-Host "🔍 Checking logs directory..." -ForegroundColor Yellow
if (-not (Test-Path "logs")) {
    Write-Host "Creating logs directory..." -ForegroundColor Yellow
    New-Item -Path "logs" -ItemType "directory" -Force | Out-Null
    Write-Host "✅ Logs directory created successfully!" -ForegroundColor Green
} else {
    Write-Host "✅ Logs directory found!" -ForegroundColor Green
}

# Start the bot
Write-Host "🚀 Starting Discord AI Bot..." -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host "The bot will now start. Follow the on-screen instructions to configure it." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the bot when you're done." -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Green

# Run the bot
python bot.py

# Wait for user to press a key before exiting
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 