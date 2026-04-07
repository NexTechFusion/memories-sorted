import os
import time
import telebot
import requests
import uuid
import json

# --- Configuration ---
# Replace with your actual bot token or set as environment variable
API_TOKEN = 'YOUR_BOT_TOKEN_HERE' 
AUTHORIZED_USER_ID = 579539601  # Dom's ID
BASE_DIR = "/root/memories-sorted"
INPUT_DIR = os.path.join(BASE_DIR, "data/input")
API_URL = "http://localhost:8373/api/upload"

bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if message.from_user.id != AUTHORIZED_USER_ID:
        bot.reply_to(message, "🚫 Unauthorized access.")
        return
    bot.reply_to(message, "📸 Memories Ingest Bot Ready.\nSend me a photo or a document to add it to your timeline.")

@bot.message_handler(commands=['status'])
def send_status(message):
    if message.from_user.id != AUTHORIZED_USER_ID: return
    try:
        r = requests.get("http://localhost:8373/api/people")
        people = r.json()
        named = len([p for p in people if p['display']])
        unnamed = len([p for p in people if not p['display']])
        bot.reply_to(message, f"📊 Status:\n- Named People: {named}\n- Unidentified: {unnamed}")
    except:
        bot.reply_to(message, "❌ API unreachable.")

@bot.message_handler(content_types=['photo', 'document'])
def handle_photos(message):
    if message.from_user.id != AUTHORIZED_USER_ID:
        bot.reply_to(message, "🚫 Unauthorized.")
        return

    try:
        # Get file info
        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id # Highest resolution
            filename = f"tg_{uuid.uuid4().hex[:8]}.jpg"
        else:
            if not message.document.mime_type.startswith('image/'):
                bot.reply_to(message, "❌ Please send an image file.")
                return
            file_id = message.document.file_id
            filename = message.document.file_name or f"tg_{uuid.uuid4().hex[:8]}.jpg"
        
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Save locally
        local_path = os.path.join(INPUT_DIR, filename)
        with open(local_path, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        bot.reply_to(message, f"📥 Received! Processing AI tags...")
        
        # Trigger API Upload/Sync
        with open(local_path, 'rb') as f:
            files = {'file': (filename, f, 'image/jpeg')}
            r = requests.post(API_URL, files=files)
            
        if r.status_code == 200:
            job_id = r.json().get('job_id')
            bot.reply_to(message, f"✅ Photo queued for AI processing. (Job: {job_id[:8]})")
        else:
            bot.reply_to(message, f"⚠️ Photo saved but API ingestion failed: {r.status_code}")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

print("🚀 Telegram Ingest Bot Starting...")
if API_TOKEN != 'YOUR_BOT_TOKEN_HERE':
    bot.infinity_polling()
else:
    print("❌ ERROR: API_TOKEN not set in telegram_ingest.py")
