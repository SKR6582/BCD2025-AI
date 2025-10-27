import discord
from discord.ext import commands
import os
import aiohttp
import json

bot = commands.Bot(command_prefix='!')
@bot.event
async def on_ready():
    print('Bot is ready')
    await bot.sync_commands()

async def run_ollama_stream(model: str, prompt: str):
    url = "http://localhost:11434/api/generate"
    payload = {"model": model, "prompt": prompt}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            async for line in resp.content:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line.decode('utf-8'))
                    if "response" in data:
                        yield data["response"]
                    if data.get("done"):
                        break
                except json.JSONDecodeError:
                    continue


@bot.event
async def on_command_error(ctx, error):
    channel_id = 1427683474042523828
    channel = bot.get_channel(channel_id)
    await channel.send(f'Error: {error}')

@bot.slash_command(name='ping', description='Legacy ping test')
async def _ping(ctx):
    latency = bot.latency
    await ctx.respond(f'Pong! {latency*1000:.2f}ms')

@bot.slash_command(name='chat', description='Chat with Ollama (stream)')
async def _chat(ctx, message: str):
    await ctx.defer()

    sent = await ctx.followup.send("생성 중...")

    output = ""
    async for token in run_ollama_stream("gemma3:4b", message):
        output += token
        if len(output) % 15 == 0:
            await sent.edit(content=f"```{output}```")


    await sent.edit(content=f"```{output}```")

if __name__ == '__main__':
    bot.run(os.getenv('DISCORD_BOT_SCB'))