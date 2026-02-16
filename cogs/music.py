import discord
from discord.ext import commands
import wavelink
from config import Config

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config()
        
    async def ensure_voice(self, ctx):
        if not ctx.author.voice:
            await ctx.send("❌ Join VC dulu!")
            return False
        if not ctx.voice_client:
            vc = await ctx.author.voice.channel.connect(cls=wavelink.Player)
            vc.autoplay = wavelink.AutoPlayMode.partial
        return True
        
    @commands.command(name='play', aliases=['p'])
    async def play(self, ctx, *, query: str = None):
        
        if not query:
            return await ctx.send("❌ Masukkan judul lagu atau link!")
            
        if not await self.ensure_voice(ctx):
            return
            
        player = ctx.voice_client
        msg = await ctx.send("🔍 Mencari...")
        
        try:
            tracks = await wavelink.Playable.search(query)
            if not tracks:
                return await msg.edit(content="❌ Tidak ditemukan!")
                
            track = tracks[0]
            
            if player.playing:
                player.queue.put(track)
                await msg.edit(content=f"✅ Ditambahkan: **{track.title}**")
            else:
                await player.play(track)
                embed = discord.Embed(
                    title="▶️ Memutar",
                    description=f"[{track.title}]({track.uri})",
                    color=self.config.EMBED_COLOR
                )
                embed.set_thumbnail(url=track.artwork or "")
                await msg.edit(content=None, embed=embed)
        except Exception as e:
            await msg.edit(content=f"❌ Error: {e}")
            
    @commands.command(name='pause')
    async def pause(self, ctx):
        player = ctx.voice_client
        if not player or not player.playing:
            return await ctx.send("❌ Tidak ada musik!")
        await player.pause(True)
        await ctx.send("⏸️ Dijeda")
        
    @commands.command(name='resume')
    async def resume(self, ctx):
        player = ctx.voice_client
        if not player or not player.paused:
            return await ctx.send("❌ Tidak dijeda!")
        await player.pause(False)
        await ctx.send("▶️ Dilanjutkan")
        
    @commands.command(name='skip', aliases=['s'])
    async def skip(self, ctx):
        player = ctx.voice_client
        if not player or not player.playing:
            return await ctx.send("❌ Tidak ada musik!")
        await player.skip()
        await ctx.send("⏭️ Dilewati")
        
    @commands.command(name='stop')
    async def stop(self, ctx):
        player = ctx.voice_client
        if not player or not player.playing:
            return await ctx.send("❌ Tidak ada musik!")
        player.queue.clear()
        await player.stop()
        await ctx.send("⏹️ Dihentikan")
        
    @commands.command(name='nowplaying', aliases=['np'])
    async def now_playing(self, ctx):
        player = ctx.voice_client
        if not player or not player.current:
            return await ctx.send("❌ Tidak ada musik!")
            
        track = player.current
        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"[{track.title}]({track.uri})",
            color=self.config.EMBED_COLOR
        )
        embed.add_field(name="Channel", value=track.author)
        embed.add_field(name="Volume", value=f"{player.volume}%")
        embed.set_thumbnail(url=track.artwork or "")
        await ctx.send(embed=embed)
        
    @commands.command(name='volume', aliases=['vol'])
    async def volume(self, ctx, vol: int = None):
        player = ctx.voice_client
        if not player:
            return await ctx.send("❌ Tidak di VC!")
        if vol is None:
            return await ctx.send(f"🔊 Volume: {player.volume}%")
        if not 0 <= vol <= 200:
            return await ctx.send("❌ 0-200!")
        await player.set_volume(vol)
        await ctx.send(f"🔊 Volume: {vol}%")
        
    @commands.command(name='disconnect', aliases=['dc'])
    async def disconnect(self, ctx):
        player = ctx.voice_client
        if not player:
            return await ctx.send("❌ Tidak di VC!")
        await player.disconnect()
        await ctx.send("👋 Bye!")

async def setup(bot):
    await bot.add_cog(Music(bot))


