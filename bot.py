import json
import threading
import time
import os
import random
import re
import requests
import logging
import sys
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)
load_dotenv()

# Configure logging
def setup_logging():
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Configure logging format
    log_format = '%(asctime)s [%(levelname)s] %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # Create logger
    logger = logging.getLogger('DiscordBot')
    logger.setLevel(logging.DEBUG)

    # Create console handler with color
    console_handler = logging.StreamHandler(sys.stdout)  # Explicitly use stdout
    console_handler.setLevel(logging.INFO)
    
    # Set encoding for Windows
    if sys.platform == 'win32':
        console_handler.stream.reconfigure(encoding='utf-8')
    
    console_formatter = ColoredFormatter(log_format, date_format)
    console_handler.setFormatter(console_formatter)

    # Create file handler for all logs
    file_handler = RotatingFileHandler(
        'logs/discord_bot.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(log_format, date_format)
    file_handler.setFormatter(file_formatter)

    # Create file handler for errors only
    error_handler = RotatingFileHandler(
        'logs/error.log',
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)

    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)

    return logger

class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels"""
    
    # Define color schemes for different components
    COLORS = {
        'DEBUG': Fore.BLUE,
        'INFO': Fore.CYAN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT,
        'SUCCESS': Fore.GREEN,
        'TIMESTAMP': Fore.MAGENTA,
        'CHANNEL': Fore.BLUE,
        'BOT': Fore.GREEN,
        'SERVER': Fore.YELLOW,
        'MESSAGE': Fore.WHITE,
        'BORDER': Fore.MAGENTA
    }

    ICONS = {
        'DEBUG': '🔍',
        'INFO': 'ℹ️',
        'WARNING': '⚠️',
        'ERROR': '🚨',
        'CRITICAL': '💥',
        'SUCCESS': '✅',
        'WAIT': '⌛',
        'BOT': '🤖',
        'SERVER': '🌐',
        'CHANNEL': '📝',
        'MESSAGE': '💬'
    }

    def format(self, record):
        # Store original message
        original_msg = record.msg
        
        # Add custom level for success messages
        if record.levelname == 'SUCCESS':
            record.levelname = 'SUCCESS'
        
        # Get base colors and icons
        level_color = self.COLORS.get(record.levelname, Fore.WHITE)
        icon = self.ICONS.get(record.levelname, '')
        
        # Format timestamp
        timestamp_color = self.COLORS['TIMESTAMP']
        record.created_fmt = f"{timestamp_color}{self.formatTime(record)}{Style.RESET_ALL}"
        
        # Format level name
        level_str = f"{level_color}[{record.levelname}]{Style.RESET_ALL}"
        
        # Process message for special formatting
        if '[Channel' in original_msg:
            # Split message into parts
            parts = original_msg.split(']', 1)
            channel_part = parts[0] + ']'
            message_part = parts[1] if len(parts) > 1 else ''
            
            # Color the channel part
            channel_part = channel_part.replace('[Channel', f"{self.COLORS['CHANNEL']}[Channel{Style.RESET_ALL}")
            
            # Add icons for specific keywords
            if 'Connected to server' in message_part:
                message_part = f"{self.ICONS['SERVER']} {message_part}"
            elif 'Bot active' in message_part:
                message_part = f"{self.ICONS['BOT']} {message_part}"
            elif 'Message sent' in message_part or 'Message received' in message_part:
                message_part = f"{self.ICONS['MESSAGE']} {message_part}"
            
            # Reconstruct message
            record.msg = f"{channel_part}{message_part}"
        
        # Add color to the message
        record.msg = f"{level_color}{icon} {record.msg}{Style.RESET_ALL}"
        
        # Format the final message
        formatted = super().format(record)
        
        # Add decorative borders for important messages
        if record.levelname in ['ERROR', 'CRITICAL', 'SUCCESS']:
            border = f"{self.COLORS['BORDER']}{'=' * 80}{Style.RESET_ALL}"
            formatted = f"\n{border}\n{formatted}\n{border}\n"
        
        return formatted

# Initialize logger
logger = setup_logging()

# Load environment variables
discord_tokens_env = os.getenv('DISCORD_TOKENS', '')
if discord_tokens_env:
    discord_tokens = [token.strip() for token in discord_tokens_env.split(',') if token.strip()]
else:
    discord_token = os.getenv('DISCORD_TOKEN')
    if not discord_token:
        logger.critical("No Discord token found! Please set DISCORD_TOKENS or DISCORD_TOKEN in .env.")
        raise ValueError("No Discord token found! Please set DISCORD_TOKENS or DISCORD_TOKEN in .env.")
    discord_tokens = [discord_token]

google_api_keys = os.getenv('GOOGLE_API_KEYS', '').split(',')
google_api_keys = [key.strip() for key in google_api_keys if key.strip()]
if not google_api_keys:
    logger.critical("No Google API Key found! Please set GOOGLE_API_KEYS in .env.")
    raise ValueError("No Google API Key found! Please set GOOGLE_API_KEYS in .env.")

processed_message_ids = set()
used_api_keys = set()
last_generated_text = None
cooldown_time = 86400

def log_message(message, level="INFO", channel_id=None):
    """Enhanced logging function with channel context and colorful formatting"""
    if channel_id:
        # Format channel ID with a decorative box
        channel_box = f"{Fore.MAGENTA}┌{'─' * (len(channel_id) + 2)}┐{Style.RESET_ALL}"
        channel_id_line = f"{Fore.MAGENTA}│ {Fore.BLUE}{channel_id}{Fore.MAGENTA} │{Style.RESET_ALL}"
        channel_box_bottom = f"{Fore.MAGENTA}└{'─' * (len(channel_id) + 2)}┘{Style.RESET_ALL}"
        channel_display = f"\n{channel_box}\n{channel_id_line}\n{channel_box_bottom}"
        
        # Add icons and colors based on message content
        if "Settings:" in message:
            message = f"⚙️ {message}"
        elif "Bot active:" in message:
            message = f"🤖 {message}"
        elif "Waiting" in message:
            if "reading messages" in message:
                message = f"📥 {message}"
            elif "next iteration" in message:
                message = f"⏳ {message}"
            else:
                message = f"⌛ {message}"
        elif "Received:" in message:
            message = f"📨 {message}"
        elif "Message sent:" in message:
            message = f"📤 {message}"
        elif "Error" in message or "Failed" in message:
            message = f"❌ {message}"
        elif "Success" in message:
            message = f"✅ {message}"
        elif "No new messages" in message:
            message = f"🔍 {message}"
        elif "Bot is running" in message:
            message = f"🚀 {message}"
        
        # Color different parts of the message
        if "Settings:" in message:
            parts = message.split("Settings:")
            message = f"{parts[0]}{Fore.CYAN}Settings:{Style.RESET_ALL}"
            settings = parts[1].split(", ")
            colored_settings = []
            for setting in settings:
                if "=" in setting:
                    key, value = setting.split("=")
                    if "Active" in value:
                        value = f"{Fore.GREEN}Active{Style.RESET_ALL}"
                    elif "No" in value:
                        value = f"{Fore.RED}No{Style.RESET_ALL}"
                    elif "Yes" in value:
                        value = f"{Fore.GREEN}Yes{Style.RESET_ALL}"
                    elif "seconds" in value:
                        value = f"{Fore.YELLOW}{value}{Style.RESET_ALL}"
                    colored_settings.append(f"{Fore.GREEN}{key.strip()}{Style.RESET_ALL} = {value}")
            message += " " + ", ".join(colored_settings)
        elif "Received:" in message:
            parts = message.split("Received:")
            message = f"{parts[0]}{Fore.CYAN}Received:{Style.RESET_ALL} {Fore.WHITE}{parts[1]}{Style.RESET_ALL}"
        elif "Message sent:" in message:
            parts = message.split("Message sent:")
            message = f"{parts[0]}{Fore.CYAN}Message sent:{Style.RESET_ALL} {Fore.GREEN}{parts[1]}{Style.RESET_ALL}"
        elif "Bot active:" in message:
            parts = message.split("Bot active:")
            message = f"{parts[0]}{Fore.CYAN}Bot active:{Style.RESET_ALL} {Fore.YELLOW}{parts[1]}{Style.RESET_ALL}"
        elif "Waiting" in message:
            parts = message.split("Waiting")
            message = f"{parts[0]}{Fore.CYAN}Waiting{Style.RESET_ALL}{parts[1]}"
        elif "No new messages" in message:
            message = f"{Fore.YELLOW}{message}{Style.RESET_ALL}"
        elif "Bot is running" in message:
            message = f"{Fore.GREEN}{message}{Style.RESET_ALL}"
        
        # Add decorative elements for important messages
        if "Message sent:" in message or "Received:" in message:
            message = f"\n{Fore.MAGENTA}{'─' * 40}{Style.RESET_ALL}\n{message}\n{Fore.MAGENTA}{'─' * 40}{Style.RESET_ALL}"
        
        message = f"{channel_display}\n{message}"
    
    if level.upper() == "SUCCESS":
        logger.info(message)
    elif level.upper() == "ERROR":
        logger.error(message)
    elif level.upper() == "WARNING":
        logger.warning(message)
    elif level.upper() == "WAIT":
        logger.info(message)
    elif level.upper() == "DEBUG":
        logger.debug(message)
    else:
        logger.info(message)

def get_random_api_key():
    available_keys = [key for key in google_api_keys if key not in used_api_keys]
    if not available_keys:
        log_message("All API keys have hit error 429. Waiting 24 hours before trying again...", "ERROR")
        time.sleep(cooldown_time)
        used_api_keys.clear()
        return get_random_api_key()
    return random.choice(available_keys)

def get_random_message_from_file():
    try:
        with open("chats.txt", "r", encoding="utf-8") as file:
            messages = [line.strip() for line in file.readlines() if line.strip()]
            return random.choice(messages) if messages else "No messages available in file."
    except FileNotFoundError:
        return "Message file chats.txt not found!"

def generate_language_specific_prompt(user_message, prompt_language):
    if prompt_language == 'en':
        return f"Reply to the following message in English: {user_message}"
    elif prompt_language == 'hi':
        return f"Reply to the following message in Hindi: {user_message}"
    else:
        log_message(f"Prompt language '{prompt_language}' is invalid. Message skipped.", "WARNING")
        return None

def generate_reply(prompt, prompt_language, use_google_ai=True):
    global last_generated_text
    if use_google_ai:
        google_api_key = get_random_api_key()
        lang_prompt = generate_language_specific_prompt(prompt, prompt_language)
        if lang_prompt is None:
            return None
        ai_prompt = f"{lang_prompt}\n\nMake it one sentence using everyday human language."
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={google_api_key}'
        headers = {'Content-Type': 'application/json'}
        data = {'contents': [{'parts': [{'text': ai_prompt}]}]}
        while True:
            try:
                response = requests.post(url, headers=headers, json=data)
                if response.status_code == 429:
                    log_message(f"API key {google_api_key} hit rate limit (429). Using another API key...", "WARNING")
                    used_api_keys.add(google_api_key)
                    return generate_reply(prompt, prompt_language, use_google_ai)
                response.raise_for_status()
                result = response.json()
                generated_text = result['candidates'][0]['content']['parts'][0]['text']
                if generated_text == last_generated_text:
                    log_message("AI generated same text, requesting new text...", "WAIT")
                    continue
                last_generated_text = generated_text
                return generated_text
            except requests.exceptions.RequestException as e:
                log_message(f"Request failed: {e}", "ERROR")
                time.sleep(2)
    else:
        return get_random_message_from_file()

def get_channel_info(channel_id, token):
    headers = {'Authorization': token}
    channel_url = f"https://discord.com/api/v9/channels/{channel_id}"
    try:
        channel_response = requests.get(channel_url, headers=headers)
        channel_response.raise_for_status()
        channel_data = channel_response.json()
        channel_name = channel_data.get('name', 'Unknown Channel')
        guild_id = channel_data.get('guild_id')
        server_name = "Direct Message"
        if guild_id:
            guild_url = f"https://discord.com/api/v9/guilds/{guild_id}"
            guild_response = requests.get(guild_url, headers=headers)
            guild_response.raise_for_status()
            guild_data = guild_response.json()
            server_name = guild_data.get('name', 'Unknown Server')
        return server_name, channel_name
    except requests.exceptions.RequestException as e:
        log_message(f"Error getting channel info: {e}", "ERROR")
        return "Unknown Server", "Unknown Channel"

def get_bot_info(token):
    headers = {'Authorization': token}
    try:
        response = requests.get("https://discord.com/api/v9/users/@me", headers=headers)
        response.raise_for_status()
        data = response.json()
        username = data.get("username", "Unknown")
        discriminator = data.get("discriminator", "")
        bot_id = data.get("id", "Unknown")
        return username, discriminator, bot_id
    except requests.exceptions.RequestException as e:
        log_message(f"Failed to get bot account info: {e}", "ERROR")
        return "Unknown", "", "Unknown"

def auto_reply(channel_id, settings, token):
    headers = {'Authorization': token}
    if settings["use_google_ai"]:
        try:
            bot_info_response = requests.get('https://discord.com/api/v9/users/@me', headers=headers)
            bot_info_response.raise_for_status()
            bot_user_id = bot_info_response.json().get('id')
        except requests.exceptions.RequestException as e:
            log_message(f"[Channel {channel_id}] Failed to get bot info: {e}", "ERROR")
            return

        while True:
            prompt = None
            reply_to_id = None
            log_message(f"[Channel {channel_id}] Waiting {settings['read_delay']} seconds before reading messages...", "WAIT")
            time.sleep(settings["read_delay"])
            try:
                response = requests.get(f'https://discord.com/api/v9/channels/{channel_id}/messages', headers=headers)
                response.raise_for_status()
                messages = response.json()
                if messages:
                    most_recent_message = messages[0]
                    message_id = most_recent_message.get('id')
                    author_id = most_recent_message.get('author', {}).get('id')
                    message_type = most_recent_message.get('type', '')
                    if author_id != bot_user_id and message_type != 8 and message_id not in processed_message_ids:
                        user_message = most_recent_message.get('content', '').strip()
                        attachments = most_recent_message.get('attachments', [])
                        if attachments or not re.search(r'\w', user_message):
                            log_message(f"[Channel {channel_id}] Message not processed (not pure text).", "WARNING")
                        else:
                            log_message(f"[Channel {channel_id}] Received: {user_message}", "INFO")
                            if settings["use_slow_mode"]:
                                slow_mode_delay = get_slow_mode_delay(channel_id, token)
                                log_message(f"[Channel {channel_id}] Slow mode active, waiting {slow_mode_delay} seconds...", "WAIT")
                                time.sleep(slow_mode_delay)
                            prompt = user_message
                            reply_to_id = message_id
                            processed_message_ids.add(message_id)
                else:
                    prompt = None
            except requests.exceptions.RequestException as e:
                log_message(f"[Channel {channel_id}] Request error: {e}", "ERROR")
                prompt = None

            if prompt:
                result = generate_reply(prompt, settings["prompt_language"], settings["use_google_ai"])
                if result is None:
                    log_message(f"[Channel {channel_id}] Invalid prompt language. Message skipped.", "WARNING")
                else:
                    response_text = result if result else "Sorry, cannot reply to message."
                    if response_text.strip().lower() == prompt.strip().lower():
                        log_message(f"[Channel {channel_id}] Reply same as received message. Not sending reply.", "WARNING")
                    else:
                        if settings["use_reply"]:
                            send_message(channel_id, response_text, token, reply_to=reply_to_id, 
                                         delete_after=settings["delete_bot_reply"], delete_immediately=settings["delete_immediately"])
                        else:
                            send_message(channel_id, response_text, token, 
                                         delete_after=settings["delete_bot_reply"], delete_immediately=settings["delete_immediately"])
            else:
                log_message(f"[Channel {channel_id}] No new messages or invalid message.", "INFO")

            log_message(f"[Channel {channel_id}] Waiting {settings['delay_interval']} seconds before next iteration...", "WAIT")
            time.sleep(settings["delay_interval"])
    else:
        while True:
            delay = settings["delay_interval"]
            log_message(f"[Channel {channel_id}] Waiting {delay} seconds before sending message from file...", "WAIT")
            time.sleep(delay)
            message_text = generate_reply("", settings["prompt_language"], use_google_ai=False)
            if settings["use_reply"]:
                send_message(channel_id, message_text, token, delete_after=settings["delete_bot_reply"], delete_immediately=settings["delete_immediately"])
            else:
                send_message(channel_id, message_text, token, delete_after=settings["delete_bot_reply"], delete_immediately=settings["delete_immediately"])

def send_message(channel_id, message_text, token, reply_to=None, delete_after=None, delete_immediately=False):
    headers = {'Authorization': token, 'Content-Type': 'application/json'}
    payload = {'content': message_text}
    if reply_to:
        payload["message_reference"] = {"message_id": reply_to}
    url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        if response.status_code in [200, 201]:
            data = response.json()
            message_id = data.get("id")
            log_message(f"[Channel {channel_id}] Message sent: \"{message_text}\" (ID: {message_id})", "SUCCESS")
            if delete_after is not None:
                if delete_immediately:
                    log_message(f"[Channel {channel_id}] Deleting message immediately without delay...", "WAIT")
                    threading.Thread(target=delete_message, args=(channel_id, message_id, token), daemon=True).start()
                elif delete_after > 0:
                    log_message(f"[Channel {channel_id}] Message will be deleted in {delete_after} seconds...", "WAIT")
                    threading.Thread(target=delayed_delete, args=(channel_id, message_id, delete_after, token), daemon=True).start()
        else:
            log_message(f"[Channel {channel_id}] Failed to send message. Status: {response.status_code}", "ERROR")
            log_message(f"[Channel {channel_id}] API Response: {response.text}", "ERROR")
    except requests.exceptions.RequestException as e:
        log_message(f"[Channel {channel_id}] Error sending message: {e}", "ERROR")

def delayed_delete(channel_id, message_id, delay, token):
    time.sleep(delay)
    delete_message(channel_id, message_id, token)

def delete_message(channel_id, message_id, token):
    headers = {'Authorization': token, 'Content-Type': 'application/json'}
    url = f'https://discord.com/api/v9/channels/{channel_id}/messages/{message_id}'
    try:
        response = requests.delete(url, headers=headers)
        if response.status_code == 204:
            log_message(f"[Channel {channel_id}] Message with ID {message_id} successfully deleted.", "SUCCESS")
        else:
            log_message(f"[Channel {channel_id}] Failed to delete message. Status: {response.status_code}", "ERROR")
            log_message(f"[Channel {channel_id}] API Response: {response.text}", "ERROR")
    except requests.exceptions.RequestException as e:
        log_message(f"[Channel {channel_id}] Error deleting message: {e}", "ERROR")

def get_slow_mode_delay(channel_id, token):
    headers = {'Authorization': token, 'Accept': 'application/json'}
    url = f"https://discord.com/api/v9/channels/{channel_id}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        slow_mode_delay = data.get("rate_limit_per_user", 0)
        log_message(f"[Channel {channel_id}] Slow mode delay: {slow_mode_delay} seconds", "INFO")
        return slow_mode_delay
    except requests.exceptions.RequestException as e:
        log_message(f"[Channel {channel_id}] Failed to get slow mode info: {e}", "ERROR")
        return 5

def print_settings_header(channel_id, channel_name, server_name):
    # Calculate the maximum width needed
    max_width = max(
        len(channel_id) + 4,
        len(channel_name) + 4,
        len(server_name) + 4,
        len("Channel Settings Configuration") + 4
    )
    
    # Create borders with consistent width
    top_border = f"{Fore.MAGENTA}╔{'═' * max_width}╗{Style.RESET_ALL}"
    bottom_border = f"{Fore.MAGENTA}╚{'═' * max_width}╝{Style.RESET_ALL}"
    side_border = f"{Fore.MAGENTA}║{Style.RESET_ALL}"
    
    # Title with decorative elements
    title = f"{Fore.CYAN}🌟 Channel Settings Configuration 🌟{Style.RESET_ALL}"
    title_padding = ' ' * ((max_width - len(title)) // 2)
    
    # Server and channel info with icons
    server_info = f"{Fore.GREEN}🌐 Server:{Style.RESET_ALL} {Fore.YELLOW}{server_name}{Style.RESET_ALL}"
    channel_details = f"{Fore.GREEN}📝 Channel:{Style.RESET_ALL} {Fore.YELLOW}{channel_name}{Style.RESET_ALL} ({Fore.BLUE}{channel_id}{Style.RESET_ALL})"
    
    # Calculate padding for each line
    server_padding = ' ' * (max_width - len(server_info) - 2)
    channel_padding = ' ' * (max_width - len(channel_details) - 2)
    
    # Print the header
    print(f"\n{top_border}")
    print(f"{side_border}{title_padding}{title}{title_padding}{side_border}")
    print(f"{side_border}{' ' * max_width}{side_border}")
    print(f"{side_border} {server_info}{server_padding}{side_border}")
    print(f"{side_border} {channel_details}{channel_padding}{side_border}")
    print(f"{bottom_border}\n")

def print_section_header(title):
    # Decorative section header with icons
    icons = {
        "AI and Language Settings": "🤖",
        "Timing Settings": "⏱️",
        "Message Settings": "💬"
    }
    icon = icons.get(title, "⚙️")
    header = f"{Fore.CYAN}{icon} {title} {icon}{Style.RESET_ALL}"
    line = f"{Fore.MAGENTA}{'─' * 3} {header} {'─' * (76 - len(header))}{Style.RESET_ALL}"
    print(f"\n{line}")

def get_yes_no_input(prompt, default='n'):
    while True:
        choice = input(f"{Fore.GREEN}❓ {prompt} {Fore.YELLOW}(y/n) [{default}]: {Style.RESET_ALL}").strip().lower() or default
        if choice in ['y', 'n']:
            return choice == 'y'
        print(f"{Fore.RED}❌ Invalid input. Please enter 'y' or 'n'.{Style.RESET_ALL}")

def get_language_input(prompt, default='en'):
    while True:
        choice = input(f"{Fore.GREEN}🌐 {prompt} {Fore.YELLOW}(en/hi) [{default}]: {Style.RESET_ALL}").strip().lower() or default
        if choice in ['en', 'hi']:
            return choice
        print(f"{Fore.RED}❌ Invalid input. Please enter 'en' or 'hi'.{Style.RESET_ALL}")

def get_number_input(prompt, min_value=0, default=None):
    while True:
        try:
            default_str = f" [{default}]" if default is not None else ""
            value = input(f"{Fore.GREEN}🔢 {prompt}{Fore.YELLOW}{default_str}: {Style.RESET_ALL}").strip()
            if not value and default is not None:
                return default
            value = int(value)
            if value >= min_value:
                return value
            print(f"{Fore.RED}❌ Please enter a number greater than or equal to {min_value}.{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}❌ Invalid input. Please enter a valid number.{Style.RESET_ALL}")

def print_settings_summary(settings):
    # Calculate the maximum width needed
    max_width = 78
    
    # Create borders with consistent width
    top_border = f"{Fore.MAGENTA}╔{'═' * max_width}╗{Style.RESET_ALL}"
    bottom_border = f"{Fore.MAGENTA}╚{'═' * max_width}╝{Style.RESET_ALL}"
    side_border = f"{Fore.MAGENTA}║{Style.RESET_ALL}"
    
    print(f"\n{top_border}")
    title = f"{Fore.CYAN}✨ Settings Summary ✨{Style.RESET_ALL}"
    title_padding = ' ' * ((max_width - len(title)) // 2)
    print(f"{side_border}{title_padding}{title}{title_padding}{side_border}")
    print(f"{side_border}{' ' * max_width}{side_border}")
    
    # AI and Language Settings
    ai_header = f"{Fore.YELLOW}🤖 AI and Language:{Style.RESET_ALL}"
    print(f"{side_border}  {ai_header}{' ' * (max_width - len(ai_header) - 4)}{side_border}")
    
    ai_settings = [
        f"Use Google Gemini AI:{Style.RESET_ALL} {Fore.CYAN}{'✅ Yes' if settings['use_google_ai'] else '❌ No'}{Style.RESET_ALL}",
        f"Language:{Style.RESET_ALL} {Fore.CYAN}{settings['prompt_language'].upper()}{Style.RESET_ALL}"
    ]
    for setting in ai_settings:
        print(f"{side_border}    {Fore.GREEN}{setting}{' ' * (max_width - len(setting) - 6)}{side_border}")
    
    # Timing Settings
    timing_header = f"{Fore.YELLOW}⏱️ Timing Settings:{Style.RESET_ALL}"
    print(f"{side_border}  {timing_header}{' ' * (max_width - len(timing_header) - 4)}{side_border}")
    
    timing_settings = []
    if settings['use_google_ai']:
        timing_settings.append(f"Message Read Delay:{Style.RESET_ALL} {Fore.CYAN}{settings['read_delay']} seconds{Style.RESET_ALL}")
    timing_settings.extend([
        f"Reply Interval:{Style.RESET_ALL} {Fore.CYAN}{settings['delay_interval']} seconds{Style.RESET_ALL}",
        f"Use Slow Mode:{Style.RESET_ALL} {Fore.CYAN}{'✅ Yes' if settings['use_slow_mode'] else '❌ No'}{Style.RESET_ALL}"
    ])
    for setting in timing_settings:
        print(f"{side_border}    {Fore.GREEN}{setting}{' ' * (max_width - len(setting) - 6)}{side_border}")
    
    # Message Settings
    msg_header = f"{Fore.YELLOW}💬 Message Settings:{Style.RESET_ALL}"
    print(f"{side_border}  {msg_header}{' ' * (max_width - len(msg_header) - 4)}{side_border}")
    
    msg_settings = [
        f"Send as Reply:{Style.RESET_ALL} {Fore.CYAN}{'✅ Yes' if settings['use_reply'] else '❌ No'}{Style.RESET_ALL}"
    ]
    if settings['delete_bot_reply'] is not None:
        delete_str = "🔄 Immediately" if settings['delete_immediately'] else f"⏳ After {settings['delete_bot_reply']} seconds"
        msg_settings.append(f"Delete Messages:{Style.RESET_ALL} {Fore.CYAN}{delete_str}{Style.RESET_ALL}")
    else:
        msg_settings.append(f"Delete Messages:{Style.RESET_ALL} {Fore.CYAN}❌ No{Style.RESET_ALL}")
    
    for setting in msg_settings:
        print(f"{side_border}    {Fore.GREEN}{setting}{' ' * (max_width - len(setting) - 6)}{side_border}")
    
    print(f"{bottom_border}")

def get_server_settings(channel_id, channel_name, server_name="Unknown Server"):
    print_settings_header(channel_id, channel_name, server_name)
    
    # AI and Language Settings
    print_section_header("AI and Language Settings")
    use_google_ai = get_yes_no_input("Use Google Gemini AI?")
    prompt_language = get_language_input("Choose prompt language", 'en')
    
    # Timing Settings
    print_section_header("Timing Settings")
    if use_google_ai:
        read_delay = get_number_input("Enter message read delay (seconds)", min_value=0, default=5)
        delay_interval = get_number_input("Enter interval (seconds) for each auto reply iteration", min_value=1, default=10)
        use_slow_mode = get_yes_no_input("Use slow mode?")
    else:
        read_delay = 0
        delay_interval = get_number_input("Enter delay (seconds) for sending messages from file", min_value=1, default=10)
        use_slow_mode = False
    
    # Message Settings
    print_section_header("Message Settings")
    use_reply = get_yes_no_input("Send message as reply?")
    delete_reply = get_yes_no_input("Delete bot reply after some time?")
    
    if delete_reply:
        delete_bot_reply = get_number_input("After how many seconds to delete reply? (0 for immediate)", min_value=0)
        delete_immediately = delete_bot_reply == 0
    else:
        delete_bot_reply = None
        delete_immediately = False
    
    settings = {
        "prompt_language": prompt_language,
        "use_google_ai": use_google_ai,
        "enable_read_message": use_google_ai,
        "read_delay": read_delay,
        "delay_interval": delay_interval,
        "use_slow_mode": use_slow_mode,
        "use_reply": use_reply,
        "delete_bot_reply": delete_bot_reply,
        "delete_immediately": delete_immediately
    }
    
    print_settings_summary(settings)
    return settings

if __name__ == "__main__":
    try:
        # Display banner
        banner = """
  ('-.      .-')    ('-. .-.             
  ( OO ).-. ( OO ). ( OO )  /             
  / . --. /(_)---\_),--. ,--. ,--. ,--.   
  | \-.  \ /    _ | |  | |  | |  | |  |   
.-'-'  |  |\  :` `. |   .|  | |  | | .-') 
 \| |_.'  | '..`''.)|       | |  |_|( OO )
  |  .-.  |.-._)   \|  .-.  | |  | | `-' /
  |  | |  |\       /|  | |  |('  '-'(_.-' 
  `--' `--' `-----' `--' `--'  `-----'    
"""
        print(f"{Fore.CYAN}{banner}{Style.RESET_ALL}")
        
        logger.info("Starting Discord Bot...")
        logger.info(f"Loaded {len(discord_tokens)} Discord tokens")
        logger.info(f"Loaded {len(google_api_keys)} Google API keys")

        bot_accounts = {}
        for token in discord_tokens:
            username, discriminator, bot_id = get_bot_info(token)
            bot_accounts[token] = {"username": username, "discriminator": discriminator, "bot_id": bot_id}
            log_message(f"Bot Account: {username}#{discriminator} (ID: {bot_id})", "SUCCESS")

        # Input channel IDs from user
        channel_ids = [cid.strip() for cid in input(f"{Fore.GREEN}Enter channel ID (separate with comma if more than one): {Style.RESET_ALL}").split(",") if cid.strip()]
        logger.info(f"Processing {len(channel_ids)} channels")

        token = discord_tokens[0]
        channel_infos = {}
        for channel_id in channel_ids:
            server_name, channel_name = get_channel_info(channel_id, token)
            channel_infos[channel_id] = {"server_name": server_name, "channel_name": channel_name}
            log_message(f"Connected to server: {server_name} | Channel Name: {channel_name}", "SUCCESS", channel_id)

        server_settings = {}
        for channel_id in channel_ids:
            info = channel_infos.get(channel_id, {})
            channel_name = info.get("channel_name", "Unknown Channel")
            server_name = info.get("server_name", "Unknown Server")
            server_settings[channel_id] = get_server_settings(channel_id, channel_name, server_name)

        for cid, settings in server_settings.items():
            info = channel_infos.get(cid, {"server_name": "Unknown Server", "channel_name": "Unknown Channel"})
            delete_str = ("Immediately" if settings['delete_immediately'] else 
                         (f"In {settings['delete_bot_reply']} seconds" if settings['delete_bot_reply'] and settings['delete_bot_reply'] > 0 else "No"))
            log_message(
                f"Settings: Gemini AI = {'Active' if settings['use_google_ai'] else 'No'}, "
                f"Language = {settings['prompt_language'].upper()}, "
                f"Read Messages = {'Active' if settings['enable_read_message'] else 'No'}, "
                f"Read Delay = {settings['read_delay']} seconds, "
                f"Interval = {settings['delay_interval']} seconds, "
                f"Slow Mode = {'Active' if settings['use_slow_mode'] else 'No'}, "
                f"Reply = {'Yes' if settings['use_reply'] else 'No'}, "
                f"Delete Message = {delete_str}",
                "INFO",
                cid
            )

        token_index = 0
        for channel_id in channel_ids:
            token = discord_tokens[token_index % len(discord_tokens)]
            token_index += 1
            bot_info = bot_accounts.get(token, {"username": "Unknown", "discriminator": "", "bot_id": "Unknown"})
            thread = threading.Thread(
                target=auto_reply,
                args=(channel_id, server_settings[channel_id], token)
            )
            thread.daemon = True
            thread.start()
            log_message(f"Bot active: {bot_info['username']}#{bot_info['discriminator']} (Token: {token[:4]}{'...' if len(token) > 4 else token})", "SUCCESS", channel_id)

        logger.info("Bot is running on multiple servers... Press CTRL+C to stop.")
        while True:
            time.sleep(10)

    except KeyboardInterrupt:
        logger.info("Bot shutdown initiated by user...")
    except Exception as e:
        logger.critical(f"Critical error occurred: {str(e)}", exc_info=True)
    finally:
        logger.info("Bot shutdown complete.")
