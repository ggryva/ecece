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
    
    LAVALINK_HOST = os.getenv('LAVALINK_HOST', 'localhost')
    LAVALINK_PORT = int(os.getenv('LAVALINK_PORT', 2333))
    LAVALINK_PASSWORD = os.getenv('LAVALINK_PASSWORD', 'youshallnotpass')
    PORT = int(os.getenv('PORT', 3000))
    
    MAX_VOLUME = 200
    DEFAULT_VOLUME = 100
