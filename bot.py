import asyncio
import logging
import os

import discord
import wavelink
from discord.ext import commands, tasks

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("JockieMusic")

logger.info(f"Wavelink version: {wavelink.__version__}")

class JockieMusic(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        
        super().__init__(
            command_prefix="g!",
            intents=intents,
            help_command=None
        )
        
        self.lavalink_connected = False
        self.node_reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
    async def setup_hook(self):
        # Load cogs
        await self.load_extension("cogs.music")
        
        # Setup Lavalink
        await self.setup_lavalink()
        
        # Start keep-alive
        self.lavalink_keepalive.start()
        
    async def setup_lavalink(self):
        """Setup Lavalink dengan wavelink 2.x"""
        try:
            # Buat node - wavelink 2.x syntax
            node = await wavelink.Node.create_node(
                bot=self,
                host="https://lavalink-3-production-94ee.up.railway.app:443",
                password=os.getenv("LAVALINK_PASSWORD", "your-password"),
                https=True,  # WSS untuk port 443
                spotify_client_id=os.getenv("SPOTIFY_CLIENT_ID"),
                spotify_client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
            )
            await wavelink.Pool.connect(client=bot, nodes=[node])
            
            logger.info(f"✅ Terhubung ke Lavalink! Node: {node.identifier}")
            self.lavalink_connected = True
            self.node_reconnect_attempts = 0
            
        except Exception as e:
            logger.error(f"❌ Gagal menghubungkan ke Lavalink: {e}")
            await self.handle_connection_failure()
    
    async def handle_connection_failure(self):
        """Retry dengan exponential backoff"""
        self.node_reconnect_attempts += 1
        
        if self.node_reconnect_attempts <= self.max_reconnect_attempts:
            delay = min(2 ** self.node_reconnect_attempts, 60)
            logger.info(f"🔄 Retry dalam {delay}s... (attempt {self.node_reconnect_attempts}/{self.max_reconnect_attempts})")
            await asyncio.sleep(delay)
            await self.setup_lavalink()
        else:
            logger.error("❌ Max retries reached")
            self.lavalink_connected = False
    
    @tasks.loop(minutes=1)
    async def lavalink_keepalive(self):
        """Keep node connection alive"""
        if not self.lavalink_connected:
            await self.setup_lavalink()
            return
            
        try:
            node = wavelink.Node.get_node()
            if not node or not node.is_connected:
                logger.warning("Node disconnected, reconnecting...")
                self.lavalink_connected = False
                await self.setup_lavalink()
        except Exception as e:
            logger.error(f"Keepalive error: {e}")
            self.lavalink_connected = False
    
    @lavalink_keepalive.before_loop
    async def before_keepalive(self):
        await self.wait_until_ready()
    
    # Event: Node connected
    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        logger.info(f"🎵 Node ready: {node.identifier}")
        self.lavalink_connected = True
    
    # Event: Node disconnected - wavelink 2.x
    @commands.Cog.listener()
    async def on_wavelink_track_end(player: wavelink.Player, track: wavelink.Playable, str):
        logger.warning(f"⚠️ Node disconnected: {node.identifier}")
        self.lavalink_connected = False
        await asyncio.sleep(5)
        await self.setup_lavalink()
    
    async def on_ready(self):
        logger.info(f"✅ {self.user} online! Guilds: {len(self.guilds)}")
    
    async def close(self):
        logger.info("🛑 Shutting down...")
        for vc in self.voice_clients:
            try:
                await vc.disconnect()
            except:
                pass
        await wavelink.Node.disconnect()
        await super().close()

# Health check server
from aiohttp import web

async def health_check(request):
    return web.Response(text="OK", status=200)

async def start_health_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 8080)))
    await site.start()
    logger.info(f"✅ Health server on port {os.getenv('PORT', 8080)}")

async def main():
    bot = JockieMusic()
    await start_health_server()
    
    try:
        await bot.start(os.getenv("DISCORD_TOKEN"))
    except KeyboardInterrupt:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
