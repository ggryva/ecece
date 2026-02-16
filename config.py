import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TOKEN = os.getenv('DISCORD_TOKEN')
    PREFIX = os.getenv('BOT_PREFIX', '!')
    EMBED_COLOR = 0x3498db
    
    EMOJIS = {
        'play': '▶️', 'pause': '⏸️', 'skip': '⏭️',
        'stop': '⏹️', 'queue': '📋', 'volume': '🔊',
        'loop': '🔁', 'shuffle': '🔀', 'search': '🔍',
        'music': '🎵', 'error': '❌', 'success': '✅'
    }
    
    # ✅ FIX 2: Konfigurasi Lavalink yang benar
    LAVALINK_HOST = os.getenv('LAVALINK_HOST', 'lavalink.dev')
    LAVALINK_PORT = int(os.getenv('LAVALINK_PORT', 443))
    LAVALINK_PASSWORD = os.getenv('LAVALINK_PASSWORD', 'https://lavalink.dev')
    
    PORT = int(os.getenv('PORT', 8080))
    MAX_VOLUME = 200
    DEFAULT_VOLUME = 100
