import discord
from discord.ext import commands
import wavelink
from config import Config

class Queue(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config()
        
    @commands.command(name='queue', aliases=['q'])
    async def show_queue(self, ctx):
        player = ctx.voice_client
        if not player or not player.queue:
            return await ctx.send("📋 Antrian kosong!")
            
        tracks = list(player.queue)[:10]
        embed = discord.Embed(
            title="📋 Antrian",
            description=f"Total: {len(player.queue)} lagu",
            color=self.config.EMBED_COLOR
        )
        
        for i, track in enumerate(tracks, 1):
            mins = track.length // 60000
            secs = (track.length // 1000) % 60
            embed.add_field(
                name=f"{i}. {track.title[:50]}",
                value=f"⏱️ {mins}:{secs:02d}",
                inline=False
            )
        await ctx.send(embed=embed)
        
    @commands.command(name='shuffle')
    async def shuffle(self, ctx):
        player = ctx.voice_client
        if not player or not player.queue:
            return await ctx.send("❌ Antrian kosong!")
        player.queue.shuffle()
        await ctx.send("🔀 Diacak!")
        
    @commands.command(name='loop')
    async def loop(self, ctx, mode: str = None):
        player = ctx.voice_client
        if not player:
            return await ctx.send("❌ Tidak di VC!")
            
        if mode is None:
            return await ctx.send(f"🔁 Mode: {player.queue.mode.name}")
            
        mode = mode.lower()
        if mode == 'off':
            player.queue.mode = wavelink.QueueMode.normal
        elif mode in ['track', 'song']:
            player.queue.mode = wavelink.QueueMode.loop
        elif mode == 'queue':
            player.queue.mode = wavelink.QueueMode.loop_all
        else:
            return await ctx.send("❌ Gunakan: off/track/queue")
            
        await ctx.send(f"🔁 Mode: {player.queue.mode.name}")
        
    @commands.command(name='clear')
    async def clear(self, ctx):
        player = ctx.voice_client
        if not player or not player.queue:
            return await ctx.send("❌ Sudah kosong!")
        player.queue.clear()
        await ctx.send("🗑️ Dibersihkan!")

async def setup(bot):
    await bot.add_cog(Queue(bot))
