import asyncio
import logging

import discord
import wavelink
from discord.ext import commands
from wavelink import Player

logger = logging.getLogger("JockieMusic")

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    def get_available_node(self):
        """Get first available node from pool"""
        try:
            if wavelink.Pool.nodes:
                return list(wavelink.Pool.nodes.values())[0]
            return None
        except Exception as e:
            logger.error(f"Error getting node: {e}")
            return None
    
    async def ensure_voice(self, ctx: commands.Context) -> bool:
        """Ensure user dan bot ada di voice channel dengan proper node checking"""
        
        # Cek apakah user di voice channel
        if not ctx.author.voice:
            await ctx.send("❌ Kamu harus join voice channel dulu!")
            return False
        
        # Cek Lavalink connection dengan retry
        node = None
        max_retries = 3
        
        for attempt in range(max_retries):
            node = self.get_available_node()
            if node:
                break
            else:
                logger.warning(f"Node tidak tersedia, attempt {attempt + 1}/{max_retries}")
                await asyncio.sleep(2)
        
        if not node:
            await ctx.send("❌ Lavalink tidak terhubung. Coba lagi nanti.")
            # Trigger reconnect
            if hasattr(self.bot, 'setup_lavalink'):
                asyncio.create_task(self.bot.setup_lavalink())
            return False
        
        # Cek apakah bot sudah di voice channel lain
        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                await ctx.send("❌ Aku sudah di channel lain!")
                return False
            return True
        
        # Connect ke voice channel
        try:
            vc = await ctx.author.voice.channel.connect(cls=Player)
            logger.info(f"Connected to voice channel: {ctx.author.voice.channel.name}")
            return True
        except Exception as e:
            logger.error(f"Gagal connect ke voice: {e}")
            await ctx.send(f"❌ Gagal join voice channel: {str(e)}")
            return False
    
    @commands.command(name="play", aliases=["p"])
    async def play(self, ctx: commands.Context, *, query: str):
        """Play music dengan proper error handling"""
        
        # Ensure voice connection
        if not await self.ensure_voice(ctx):
            return
        
        vc: Player = ctx.voice_client
        
        # Cek node lagi sebelum play
        if not self.get_available_node():
            await ctx.send("❌ Node tidak tersedia. Reconnecting...")
            return
        
        try:
            # Search track - wavelink 3.x syntax
            tracks = await wavelink.Playable.search(query)
            
            if not tracks:
                await ctx.send(f"❌ Tidak menemukan: `{query}`")
                return
            
            # Play track
            if isinstance(tracks, wavelink.Playlist):
                # Jika playlist
                for track in tracks.tracks[:50]:  # Limit 50 tracks
                    await vc.queue.put_wait(track)
                await ctx.send(f"🎵 Menambahkan playlist **{tracks.name}** ({len(tracks.tracks)} lagu)")
            else:
                # Single track
                track = tracks[0]
                await vc.queue.put_wait(track)
                await ctx.send(f"🎵 Menambahkan: **{track.title}** - {track.author}")
            
            # Start playing jika belum play
            if not vc.playing:
                await vc.play(vc.queue.get())
                
        except wavelink.LavalinkException as e:
            logger.error(f"Lavalink error: {e}")
            await ctx.send(f"❌ Error Lavalink: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error di play: {e}")
            await ctx.send(f"❌ Error: {str(e)}")
    
    @commands.command(name="stop", aliases=["leave", "disconnect"])
    async def stop(self, ctx: commands.Context):
        """Stop dan disconnect"""
        if not ctx.voice_client:
            await ctx.send("❌ Aku tidak di voice channel!")
            return
        
        vc: Player = ctx.voice_client
        await vc.disconnect()
        await ctx.send("👋 Sampai jumpa!")
    
    @commands.command(name="skip", aliases=["s"])
    async def skip(self, ctx: commands.Context):
        """Skip current track"""
        if not ctx.voice_client:
            await ctx.send("❌ Tidak ada yang diputar!")
            return
        
        vc: Player = ctx.voice_client
        
        if not vc.playing:
            await ctx.send("❌ Tidak ada yang diputar!")
            return
        
        await vc.skip()
        await ctx.send("⏭️ Skip!")
    
    @commands.command(name="queue", aliases=["q"])
    async def queue(self, ctx: commands.Context):
        """Show current queue"""
        if not ctx.voice_client:
            await ctx.send("❌ Tidak ada yang diputar!")
            return
        
        vc: Player = ctx.voice_client
        
        if vc.queue.is_empty:
            await ctx.send("📭 Queue kosong!")
            return
        
        queue_list = []
        for i, track in enumerate(list(vc.queue)[:10], 1):
            queue_list.append(f"{i}. {track.title} - {track.author}")
        
        await ctx.send(f"📋 **Queue:**\n" + "\n".join(queue_list))
    
    # Event listeners untuk wavelink 3.x
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        """Auto play next track dari queue"""
        if not payload.player:
            return
        
        vc: Player = payload.player
        
        # Play next track jika ada di queue
        if not vc.queue.is_empty:
            try:
                next_track = vc.queue.get()
                await vc.play(next_track)
                logger.info(f"Auto-play next: {next_track.title}")
            except Exception as e:
                logger.error(f"Error auto-playing next track: {e}")
    
    @commands.Cog.listener()
    async def on_wavelink_track_exception(self, payload: wavelink.TrackExceptionEventPayload):
        """Handle track errors"""
        logger.error(f"Track exception: {payload.exception}")
        if payload.player and not payload.player.queue.is_empty:
            try:
                await payload.player.skip()
            except Exception as e:
                logger.error(f"Error skipping track: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
    logger.info("Music cog loaded!")
