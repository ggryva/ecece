import asyncio
import logging

import discord
import wavelink
from discord.ext import commands

logger = logging.getLogger("JockieMusic")

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    async def ensure_voice(self, ctx: commands.Context) -> bool:
        """Ensure user and bot are in voice channel"""
        
        if not ctx.author.voice:
            await ctx.send("❌ Join voice channel dulu!")
            return False
        
        # Check Lavalink connection
        try:
            node = wavelink.NodePool.get_node()
            if not node or not node.is_connected:
                await ctx.send("❌ Lavalink tidak terhubung. Coba lagi nanti.")
                return False
        except Exception as e:
            logger.error(f"Node check error: {e}")
            await ctx.send("❌ Lavalink error. Coba lagi nanti.")
            return False
        
        # Check if bot already in different channel
        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                await ctx.send("❌ Aku sudah di channel lain!")
                return False
            return True
        
        # Connect to voice
        try:
            vc = await ctx.author.voice.channel.connect(cls=wavelink.Player)
            logger.info(f"Connected to: {ctx.author.voice.channel.name}")
            return True
        except Exception as e:
            logger.error(f"Voice connect error: {e}")
            await ctx.send(f"❌ Gagal join: {str(e)}")
            return False
    
    @commands.command(name="play", aliases=["p"])
    async def play(self, ctx: commands.Context, *, query: str):
        """Play music"""
        
        if not await self.ensure_voice(ctx):
            return
        
        vc: wavelink.Player = ctx.voice_client
        
        # Check node again
        try:
            node = wavelink.NodePool.get_node()
            if not node or not node.is_connected:
                await ctx.send("❌ Lavalink not connected!")
                return
        except:
            await ctx.send("❌ Lavalink error!")
            return
        
        try:
            # Search - wavelink 2.x syntax
            tracks = await wavelink.YouTubeTrack.search(query)
            
            if not tracks:
                await ctx.send(f"❌ Tidak menemukan: `{query}`")
                return
            
            track = tracks[0]
            
            # Play
            if vc.is_playing():
                await vc.queue.put_wait(track)
                await ctx.send(f"🎵 Added to queue: **{track.title}** - {track.author}")
            else:
                await vc.play(track)
                await ctx.send(f"🎵 Now playing: **{track.title}** - {track.author}")
                
        except Exception as e:
            logger.error(f"Play error: {e}")
            await ctx.send(f"❌ Error: {str(e)}")
    
    @commands.command(name="stop", aliases=["leave", "disconnect"])
    async def stop(self, ctx: commands.Context):
        """Stop and leave"""
        if not ctx.voice_client:
            await ctx.send("❌ Tidak di voice channel!")
            return
        
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Bye!")
    
    @commands.command(name="skip", aliases=["s"])
    async def skip(self, ctx: commands.Context):
        """Skip track"""
        if not ctx.voice_client:
            await ctx.send("❌ Tidak ada yang diputar!")
            return
        
        vc: wavelink.Player = ctx.voice_client
        
        if not vc.is_playing():
            await ctx.send("❌ Tidak ada yang diputar!")
            return
        
        await vc.stop()
        await ctx.send("⏭️ Skipped!")
    
    @commands.command(name="queue", aliases=["q"])
    async def queue(self, ctx: commands.Context):
        """Show queue"""
        if not ctx.voice_client:
            await ctx.send("❌ Tidak ada yang diputar!")
            return
        
        vc: wavelink.Player = ctx.voice_client
        
        if vc.queue.is_empty:
            await ctx.send("📭 Queue kosong!")
            return
        
        queue_list = []
        for i, track in enumerate(list(vc.queue)[:10], 1):
            queue_list.append(f"{i}. {track.title} - {track.author}")
        
        await ctx.send(f"📋 **Queue:**\n" + "\n".join(queue_list))
    
    # Events - wavelink 2.x
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player: wavelink.Player, track: wavelink.YouTubeTrack, reason: str):
        """Auto play next"""
        if not player.queue.is_empty:
            try:
                next_track = player.queue.get()
                await player.play(next_track)
                logger.info(f"Auto-play: {next_track.title}")
            except Exception as e:
                logger.error(f"Auto-play error: {e}")
    
    @commands.Cog.listener()
    async def on_wavelink_track_exception(self, player: wavelink.Player, track: wavelink.YouTubeTrack, error: Exception):
        """Handle track error"""
        logger.error(f"Track exception: {error}")
        if not player.queue.is_empty:
            try:
                await player.stop()
            except:
                pass

async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
    logger.info("Music cog loaded!")
