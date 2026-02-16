import discord
from discord.ext import commands
from config import Config

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config()
        
    @commands.command(name='stats')
    async def stats(self, ctx):
        embed = discord.Embed(title="📊 Stats", color=self.config.EMBED_COLOR)
        embed.add_field(name="Server", value=len(self.bot.guilds))
        embed.add_field(name="VC Aktif", value=len(self.bot.voice_clients))
        embed.add_field(name="Ping", value=f"{round(self.bot.latency*1000)}ms")
        embed.add_field(name="Host", value="Railway 🚀")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Admin(bot))
