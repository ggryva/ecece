import asyncio
import logging
import os
from datetime import datetime

import discord
import wavelink
from discord.ext import commands, tasks
from wavelink import Node

# Setup logging yang benar
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("JockieMusic")

class JockieMusic(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )
        
        self.lavalink_connected = False
        self.node_reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
    async def setup_hook(self):
        # Load cogs
        await self.load_extension("cogs.music")
        
        # Setup Lavalink dengan retry logic
        await self.setup_lavalink()
        
        # Start keep-alive task
        self.lavalink_keepalive.start()
        
    async def setup_lavalink(self):
        """Setup Lavalink dengan proper error handling dan retry"""
        try:
            # Konfigurasi node - wavelink 3.x syntax
            node = Node(
                uri=os.getenv("LAVALINK_URI", "https://lavalink-3-production-94ee.up.railway.app:443"),
                password=os.getenv("LAVALINK_PASSWORD", "your-password"),
                identifier=f"JockieNode-{datetime.now().timestamp()}"
            )
            
            logger.info("Menghubungkan ke Lavalink...")
            
            # Connect dengan timeout - wavelink 3.x syntax
            await wavelink.Pool.connect(nodes=[node], client=self)
            
            # Verifikasi koneksi benar-benar berhasil
            await asyncio.sleep(2)  # Tunggu handshake selesai
            
            # Cek node yang tersedia
            nodes = wavelink.Pool.nodes
            if nodes:
                self.lavalink_connected = True
                self.node_reconnect_attempts = 0
                logger.info(f"✅ Terhubung ke Lavalink! Nodes: {len(nodes)}")
            else:
                raise Exception("No nodes available after connection")
                
        except asyncio.TimeoutError:
            logger.error("❌ Timeout saat menghubungkan ke Lavalink")
            await self.handle_connection_failure()
        except Exception as e:
            logger.error(f"❌ Gagal menghubungkan ke Lavalink: {e}")
            await self.handle_connection_failure()
    
    async def handle_connection_failure(self):
        """Handle failed connection dengan exponential backoff"""
        self.node_reconnect_attempts += 1
        
        if self.node_reconnect_attempts <= self.max_reconnect_attempts:
            delay = min(2 ** self.node_reconnect_attempts, 60)  # Max 60 detik
            logger.info(f"🔄 Mencoba reconnect dalam {delay} detik... (attempt {self.node_reconnect_attempts}/{self.max_reconnect_attempts})")
            
            await asyncio.sleep(delay)
            await self.setup_lavalink()
        else:
            logger.error("❌ Max reconnect attempts reached. Lavalink tidak tersedia.")
            self.lavalink_connected = False
    
    @tasks.loop(minutes=1)
    async def lavalink_keepalive(self):
        """Keep-alive untuk mencegah Railway sleep"""
        if not self.lavalink_connected:
            logger.warning("Lavalink tidak terhubung, mencoba reconnect...")
            await self.setup_lavalink()
            return
            
        try:
            # Cek node yang tersedia
            nodes = wavelink.Pool.nodes
            if not nodes:
                logger.warning("Tidak ada nodes tersedia, reconnecting...")
                self.lavalink_connected = False
                await self.setup_lavalink()
            else:
                logger.debug(f"Keep-alive check: {len(nodes)} nodes available")
        except Exception as e:
            logger.error(f"Error dalam keepalive: {e}")
            self.lavalink_connected = False
    
    @lavalink_keepalive.before_loop
    async def before_keepalive(self):
        await self.wait_until_ready()
    
    # Event listeners untuk wavelink 3.x
    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload):
        """Event handler saat node ready"""
        logger.info(f"🎵 Node Ready: {payload.node.identifier}")
        logger.info(f"   - Resumed: {payload.resumed}")
        logger.info(f"   - Session ID: {payload.session_id}")
        self.lavalink_connected = True
        self.node_reconnect_attempts = 0
    
    # PERBAIKAN: Gunakan event yang benar untuk wavelink 3.x
    @commands.Cog.listener()
    async def on_wavelink_node_disconnected(self, payload: wavelink.NodeDisconnectedPayload):
        """Event handler saat node disconnect - wavelink 3.x"""
        logger.warning(f"⚠️ Node Disconnected: {payload.node.identifier}")
        logger.warning(f"   - Reason: {getattr(payload, 'reason', 'Unknown')}")
        self.lavalink_connected = False
        
        # Trigger reconnect
        await asyncio.sleep(5)
        await self.setup_lavalink()
    
    async def close(self):
        """Cleanup saat bot shutdown"""
        logger.info("🛑 Menutup bot...")
        
        # Close semua voice connections
        for vc in self.voice_clients:
            await vc.disconnect()
        
        # Disconnect dari Lavalink
        try:
            await wavelink.Pool.close()
            logger.info("✅ Lavalink pool ditutup")
        except Exception as e:
            logger.error(f"Error menutup pool: {e}")
        
        # Close aiohttp sessions
        await super().close()
        logger.info("✅ Bot ditutup dengan aman")

# Health check server untuk Railway
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
    logger.info(f"✅ Health check server berjalan di port {os.getenv('PORT', 8080)}")

async def main():
    bot = JockieMusic()
    
    # Start health check server
    await start_health_server()
    
    # Run bot
    try:
        await bot.start(os.getenv("DISCORD_TOKEN"))
    except KeyboardInterrupt:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
