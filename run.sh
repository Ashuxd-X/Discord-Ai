#!/bin/bash

# Discord AI Bot - Auto-Install and Run Script
# This script will automatically install dependencies, set up the environment, and start the bot

# Set text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Print header
echo -e "${CYAN}============================================="
echo -e "${GREEN}[BOT] Discord AI Bot - Auto-Install and Run Script"
echo -e "${CYAN}=============================================${NC}"
echo

# Check if Python is installed
echo -e "${YELLOW}[CHECK] Checking Python installation...${NC}"
if command -v python3 &>/dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}[SUCCESS] Python is installed: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}[ERROR] Python is not installed or not in PATH!${NC}"
    echo "Please install Python from https://www.python.org/downloads/"
    echo "Make sure to check 'Add Python to PATH' during installation."
    echo
    echo "Press Enter to exit..."
    read
    exit 1
fi

# Check if pip is installed
echo
echo -e "${YELLOW}[CHECK] Checking pip installation...${NC}"
if command -v pip3 &>/dev/null; then
    PIP_VERSION=$(pip3 --version)
    echo -e "${GREEN}[SUCCESS] pip is installed: $PIP_VERSION${NC}"
else
    echo -e "${RED}[ERROR] pip is not installed or not in PATH!${NC}"
    echo "Please install pip or reinstall Python."
    echo
    echo "Press Enter to exit..."
    read
    exit 1
fi

# Install required packages
echo
echo -e "${YELLOW}[INSTALL] Installing required packages...${NC}"
pip3 install -r requirements.txt >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Failed to install packages!${NC}"
    echo
    echo "Press Enter to exit..."
    read
    exit 1
else
    echo -e "${GREEN}[SUCCESS] Packages installed successfully!${NC}"
fi

# Check if .env file exists
echo
echo -e "${YELLOW}[CHECK] Checking .env file...${NC}"
if [ ! -f .env ]; then
    echo -e "${YELLOW}[WARNING] .env file not found!${NC}"
    echo "Creating a new .env file..."
    
    # Create .env file
    touch .env
    
    # Ask for Discord token
    echo -e "${CYAN}Please enter your Discord bot token:${NC}"
    read discord_token
    
    # Ask for Google API key
    echo -e "${CYAN}Please enter your Google API key:${NC}"
    read google_api_key
    
    # Write to .env file
    echo "DISCORD_TOKENS=$discord_token" > .env
    echo "GOOGLE_API_KEYS=$google_api_key" >> .env
    
    echo -e "${GREEN}[SUCCESS] .env file created successfully!${NC}"
else
    echo -e "${GREEN}[SUCCESS] .env file found!${NC}"
    
    # Check if .env file has required variables
    if ! grep -q "DISCORD_TOKENS=" .env; then
        echo -e "${YELLOW}[WARNING] DISCORD_TOKENS not found in .env file!${NC}"
        echo -e "${CYAN}Please enter your Discord bot token:${NC}"
        read discord_token
        echo "DISCORD_TOKENS=$discord_token" >> .env
    fi
    
    if ! grep -q "GOOGLE_API_KEYS=" .env; then
        echo -e "${YELLOW}[WARNING] GOOGLE_API_KEYS not found in .env file!${NC}"
        echo -e "${CYAN}Please enter your Google API key:${NC}"
        read google_api_key
        echo "GOOGLE_API_KEYS=$google_api_key" >> .env
    fi
fi

# Check if logs directory exists
echo
echo -e "${YELLOW}[CHECK] Checking logs directory...${NC}"
if [ ! -d logs ]; then
    echo "Creating logs directory..."
    mkdir logs
    echo -e "${GREEN}[SUCCESS] Logs directory created successfully!${NC}"
else
    echo -e "${GREEN}[SUCCESS] Logs directory found!${NC}"
fi

# Start the bot
echo
echo -e "${CYAN}============================================="
echo -e "${GREEN}[START] Starting Discord AI Bot..."
echo -e "${CYAN}=============================================${NC}"
echo "The bot will now start. Follow the on-screen instructions to configure it."
echo "Press Ctrl+C to stop the bot when you're done."
echo -e "${CYAN}=============================================${NC}"
echo

# Run the bot
python3 bot.py

# Wait for user to press Enter before exiting
echo
echo "Press Enter to exit..."
read 