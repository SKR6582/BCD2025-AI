import db_module.score as score
import discord
from discord.ext import commands
import os


bot = commands.Bot(command_prefix="!")
@bot.event
async def on_ready(ctx):
    print("run")
    await bot.sync_command()

@bot.slash_command(name="leaderboard")
async def leaderboard(ctx):
    embed = discord.Embed(
        title = "리더보드",
        description = "상위 10명의 값을 가져옵니다.",
        color=discord.Color.blue()
    )
    for arr in score.get_ranking_by_difficulty(difficulty=1) :
        embed.add_field(
            name = arr["classid"],
            value = arr["score"],
            inline = False
        )


    await ctx.respond(embed=embed)

bot.run(os.environ["DISCORD_BOT_SCB"])