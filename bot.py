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
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        
        super().__init__(
            command_prefix=Config.PREFIX,
            intents=intents,
            help_command=None
        )
        
        self.config = Config()
        
    async def setup_hook(self):
        logger.info("Menghubungkan ke Lavalink...")
        
        connected = False
        retries = 10
        while not connected and retries > 0:
            try:
                node = wavelink.Node(
                    uri=f'http://{self.config.LAVALINK_HOST}:{self.config.LAVALINK_PORT}',
                    password=self.config.LAVALINK_PASSWORD,
                    secure=True
                )
                await wavelink.Pool.connect(client=self, nodes=[node])
                connected = True
                logger.info("Terhubung ke Lavalink!")
            except Exception as e:
                logger.error(f"Retry {retries}: {e}")
                retries -= 1
                await asyncio.sleep(5)
        
        if not connected:
            raise Exception("Gagal konek ke Lavalink!")
            
        await self.load_extension('cogs.music')
        await self.load_extension('cogs.queue')
        await self.load_extension('cogs.admin')
        
    async def on_ready(self):
        logger.info(f'{self.user} online!')
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name=f"{self.config.PREFIX}help | Railway"
            )
        )
        
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload):
        logger.info(f'Lavalink ready: {payload.node.uri}')

async def start_web_server(bot):
    """Health check server"""
    async def health(request):
        return web.Response(text="Bot is running!", status=200)
    
    app = web.Application()
    app.router.add_get('/', health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', bot.config.PORT)
    await site.start()
    logger.info(f"Health check: port {bot.config.PORT}")

async def main_async():
    """Main async function"""
    bot = JockieMusic()
    
    @bot.command(name='help')
    async def help_cmd(ctx):
        emojis = bot.config.EMOJIS
        embed = discord.Embed(
            title=f"{emojis['music']} Jockie Music",
            description=f"Prefix: `{bot.config.PREFIX}`",
            color=bot.config.EMBED_COLOR
        )
        embed.add_field(name="Musik", value="`play` `pause` `resume` `skip` `stop` `np` `volume`", inline=False)
        embed.add_field(name="Antrian", value="`queue` `shuffle` `loop` `clear`", inline=False)
        embed.add_field(name="Info", value="`stats` `disconnect`", inline=False)
        await ctx.send(embed=embed)
    
    # Jalankan web server dan bot secara parallel
    await asyncio.gather(
        start_web_server(bot),
        bot.start(bot.config.TOKEN)
    )

def main():
    """Entry point"""
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
