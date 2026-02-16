import discord
from discord.ext import commands
import asyncio
import logging
import wavelink
from aiohttp import web
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('JockieMusic')

class JockieMusic(commands.Bot):
    def __init__(self):
        # ✅ FIX: Intents harus di-enable di Developer Portal!
        intents = discord.Intents.default()
        intents.message_content = True  # Privileged Intent
        intents.members = True          # Privileged Intent  
        intents.presences = True        # Privileged Intent
        intents.voice_states = True
        
        super().__init__(
            command_prefix=Config.PREFIX,
            intents=intents,
            help_command=None
        )
        
        self.config = Config()
        
    async def setup_hook(self):
        logger.info("Menghubungkan ke Lavalink...")
        
        # ✅ FIX: Wavelink v4 syntax
        node = wavelink.Node(
            uri=f'https://{self.config.LAVALINK_HOST}:{self.config.LAVALINK_PORT}',
            password=self.config.LAVALINK_PASSWORD
        )
        
        try:
            await wavelink.Pool.connect(client=self, nodes=[node])
            logger.info("✅ Terhubung ke Lavalink!")
        except Exception as e:
            logger.error(f"❌ Gagal konek: {e}")
            raise

    async def on_ready(self):
        logger.info(f'🚀 {self.user} online!')
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name=f"{self.config.PREFIX}help | Railway"
            )
        )

    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload):
        logger.info(f'🎵 Lavalink ready: {payload.node.uri}')

async def start_web_server(bot):
    async def health(request):
        return web.Response(text="Bot OK!", status=200)
    
    app = web.Application()
    app.router.add_get('/', health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', bot.config.PORT)
    await site.start()
    logger.info(f"🌐 Health check: port {bot.config.PORT}")

async def main_async():
    bot = JockieMusic()
    
    @bot.command(name='help')
    async def help_cmd(ctx):
        emojis = bot.config.EMOJIS
        embed = discord.Embed(
            title=f"{emojis['music']} Jockie Music",
            description=f"Prefix: `{bot.config.PREFIX}`",
            color=bot.config.EMBED_COLOR
        )
        embed.add_field(name="🎵 Musik", value="`play` `pause` `resume` `skip` `stop` `np` `volume`", inline=False)
        embed.add_field(name="📋 Antrian", value="`queue` `shuffle` `loop` `clear`", inline=False)
        await ctx.send(embed=embed)
    
    await asyncio.gather(
        start_web_server(bot),
        bot.start(bot.config.TOKEN)
    )

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
